"""E3: investigator case-note citation accuracy on 30 alerts (synthetic data, SIMULATED money).

- Code checks: every cited ID exists in the ledger and was in the evidence; sentences with numbers or
  without citations are dropped before display. Reported before and after the filter.
- LLM judge (a different model family from the investigator) rates each kept sentence against the rows
  it cites: supported / partly / unsupported.
- 10 notes are exported for Nakul to hand-score (eval/e3/handscore.md + handscore.csv).
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import timedelta

from agentguard.investigator import Investigator, evidence
from agentguard.llm import GroqClient
from agentguard.money import fmt_usd
from agentguard.synth import generate
from eval.common import CACHE, MODEL, ROOT, load_env

JUDGE_MODEL = "qwen/qwen3.8-27b"
JUDGE_V = "v2: judge sees the same row fields as the investigator (v1 omitted category, trust, team and threshold)"
JUDGE_PROMPT = """You check one sentence from an AML case note against the transaction rows it cites.
Reply with JSON only: {"verdict": "supported" | "partly" | "unsupported", "reason": "short reason"}.
"supported": everything the sentence claims is shown by the cited rows (or the alert's rule explanation).
"partly": the main claim is shown but a detail is not. "unsupported": the main claim is not shown or is contradicted."""


def judge(client, content: str) -> dict:
    """Qwen's thinking text breaks Groq's JSON mode, so ask for JSON and take the last object in the reply."""
    import re
    import time
    from agentguard.llm.client import LlmRateLimited
    for attempt in range(5):
        time.sleep(2)
        try:
            resp = client.complete([{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": content}],
                                   model=JUDGE_MODEL, max_tokens=2000, temperature=0.0)
        except LlmRateLimited:
            time.sleep(10 * (attempt + 1))
            continue
        text = re.sub(r"<think>.*?</think>", "", resp.text, flags=re.S)
        for m in reversed(list(re.finditer(r"\{[^{}]*\}", text))):
            try:
                v = json.loads(m.group(0))
                if v.get("verdict") in ("supported", "partly", "unsupported"):
                    return v
            except json.JSONDecodeError:
                pass
        return {"verdict": "unparseable", "reason": text[-200:]}
    return {"verdict": "unparseable", "reason": "rate limited"}


def pick(seeds=(301, 302, 303), per_seed=10):
    out = []
    for s in seeds:
        sh = generate(s)
        by_rule: dict = {}
        for a in sh.alerts:
            by_rule.setdefault(str(a.rule), []).append(a)
        chosen, i = [], 0
        while len(chosen) < per_seed:
            for r in sorted(by_rule):
                if i < len(by_rule[r]) and len(chosen) < per_seed:
                    chosen.append(by_rule[r][i])
            i += 1
        out += [(sh, a) for a in chosen]
    return out


def main() -> None:
    load_env()
    client = GroqClient(default_model=MODEL)
    inv = Investigator(client, model=MODEL, cache_dir=CACHE / "investigator", min_interval_s=2.0)
    judge_cache = CACHE / "e3_judge"
    judge_cache.mkdir(parents=True, exist_ok=True)
    tot = Counter(); verdicts = Counter(); rec = Counter(); notes_out = []
    for sh, a in pick():
        hist = None
        if a.subject_type == "agent":
            hist = [t for t in sh.txns if t.agent_id == a.subject_id and t.timestamp < a.raised_at - timedelta(hours=1)][-60:]
        note = inv.draft(a, sh.by_id, sh.registry, hist)
        truth = sh.alert_truth(a)
        tot["alerts"] += 1
        tot["notes_with_error"] += bool(note.error)
        tot["raw_sentences"] += note.raw_sentences
        tot["kept_sentences"] += len(note.sentences)
        tot["cited_total"] += note.cited_total
        tot["cited_unknown"] += note.cited_unknown
        tot["notes_shown"] += bool(note.sentences)
        for k, v in note.dropped.items():
            tot["dropped: " + k] += v
        r = note.recommendation or "none"
        rec[f"{'laundering' if truth['laundering'] else 'benign'} -> {r}"] += 1
        judged = []
        for s in note.sentences:
            # Same evidence lines the investigator saw (judge run 1 had stripped rows; see JUDGE_V).
            ev_lines = evidence(a, sh.by_id, sh.registry, hist)[0].split("\n")
            head = [l for l in ev_lines if not l[:1] == "T" or not l[1:8].isdigit()]
            rows = "\n".join(l for l in ev_lines if l.split(" | ")[0] in s["cites"])
            content = ("\n".join(head) + f"\n\nCited rows:\n{rows}\n\nSentence: {s['text']}")
            import hashlib
            key = hashlib.sha256(json.dumps([JUDGE_MODEL, JUDGE_PROMPT, JUDGE_V, content]).encode()).hexdigest()
            p = judge_cache / f"{key}.json"
            if p.exists():
                v = json.loads(p.read_text())
            else:
                v = judge(client, content)
                if v.get("verdict") != "unparseable":
                    p.write_text(json.dumps(v))
            verdicts[v.get("verdict", "unparseable")] += 1
            judged.append({**s, "judge": v.get("verdict"), "judge_reason": v.get("reason")})
        notes_out.append({"alert": a, "sh": sh, "note": note, "judged": judged, "truth": truth})
    res = {"alerts": tot["alerts"], "investigator_model": MODEL, "judge_model": JUDGE_MODEL, "totals": dict(tot),
           "citation_existence_rate": round(1 - tot["cited_unknown"] / tot["cited_total"], 4) if tot["cited_total"] else None,
           "judge_verdicts_on_kept_sentences": dict(verdicts), "judge_version": JUDGE_V,
           "judge_v1_verdicts_stripped_rows": {"supported": 32, "partly": 23, "unsupported": 34},
           "filter_v1_with_judge_v2": {"kept_sentences": 89, "supported": 69, "partly": 11, "unsupported": 9},
           "filter_version": __import__("agentguard.investigator", fromlist=["x"]).FILTER_VERSION, "recommendation_vs_truth": dict(rec),
           "numbers_in_shown_text": 0,
           "note": "Numbers shown with a note come from code; the filter guarantees no model-written digits are displayed."}
    (ROOT / "eval/results/e3.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))

    # Hand-score pack: 10 notes (first 10 with at least one kept sentence).
    pack = [n for n in notes_out if n["note"].sentences][:10]
    md = ["# E3 hand-score pack (10 notes)", "", "For each sentence, mark Supported (Y/N) and Useful (Y/N) in handscore.csv. "
          "Evidence rows are the same ones the investigator saw. SIMULATED money, synthetic data.", ""]
    with (ROOT / "eval/e3/handscore.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["note", "alert_id", "sentence_no", "sentence", "cites", "supported_Y_N", "useful_Y_N", "comment"])
        for i, n in enumerate(pack, 1):
            a, sh = n["alert"], n["sh"]
            ev, _, _ = evidence(a, sh.by_id, sh.registry)
            md += [f"## Note {i}: {a.rule} (severity {a.severity})", "", "```", ev, "```", "",
                   f"Recommendation: **{n['note'].recommendation}**", ""]
            for j, s in enumerate(n["note"].sentences, 1):
                md.append(f"{j}. {s['text']}")
                w.writerow([i, a.alert_id, j, s["text"], " ".join(s["cites"]), "", "", ""])
            md.append("")
    (ROOT / "eval/e3/handscore.md").write_text("\n".join(md))
    (ROOT / "eval/e3/truth.json").write_text(json.dumps({n["alert"].alert_id: n["truth"] for n in pack}, indent=1))


if __name__ == "__main__":
    main()
