"""E3 v4: investigator v4 case notes on 31 alerts (synth-v2 data) plus the frozen reference case. SIMULATED money.

- Code checks (agentguard.investigator.verify): cited evidence IDs exist; no model-written numbers; claim checks
  (just under >= 80% of threshold, burst <= 10 min, short period <= 24 h); doubts only as questions; no excuses.
- LLM judge (a different model family) rates each kept claim line (summary, evidence, reason) against the pack
  lines it cites: supported / partly / unsupported, and whether it contradicts the rule.
- Automatic usefulness checklist per note (code, not a human score): limit proximity, time window, merchant
  concentration, cross-alert links, recommendation with a reason, next steps. Counted only where applicable.
- Hand-score pack v4: eval/e3/handscore_v4.md + .csv (note 1 = frozen reference case A6c2d42955a).
Earlier results are kept unchanged: eval/results/e3_v1.json, e3_v2.json, e3_v3_prompt_only.json, e3_v3.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter
from datetime import timedelta

from agentguard import evidence as ev_mod
from agentguard import investigator as inv_mod
from agentguard.evidence import build
from agentguard.investigator import Investigator
from agentguard.llm import GroqClient
from agentguard.llm.client import LlmRateLimited
from agentguard.synth import DATA_VERSION, generate
from eval.common import CACHE, MODEL, ROOT, load_env
from eval.e3 import reference

JUDGE_MODEL = "qwen/qwen3.8-27b"
JUDGE_V = "v4: judges one note line against the evidence-pack lines it cites (pack figures computed by code)"
JUDGE_PROMPT = """You check one line from an AML case note against the evidence lines it cites. The evidence lines were
computed by code from the ledger and are true.
Reply with JSON only: {"verdict": "supported" | "partly" | "unsupported", "contradicts_rule": true | false, "reason": "short reason"}.
"contradicts_rule" is true if the line disputes the rule explanation, or calls the very pattern the rule detected routine,
normal or legitimate.
"supported": everything the line claims is shown by the cited evidence lines (or the rule explanation).
"partly": the main claim is shown but a detail is not. "unsupported": the main claim is not shown or is contradicted."""
CHECKS = ("limit_proximity", "time_window", "merchant_concentration", "cross_alert_links", "recommendation_with_reason", "next_steps")
CLAIM_SECTIONS = ("summary", "evidence", "reason")


def judge(client, content: str) -> dict:
    """Qwen's thinking text breaks Groq's JSON mode, so ask for JSON and take the last object in the reply."""
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


def checklist(note, pack) -> dict[str, bool | None]:
    """True/False where the item applies to this alert, None where it does not."""
    kind = {f.id: f.kind for f in pack.facts}
    cited = {kind[c] for sec in ("summary", "evidence", "reason", "actions") for x in note.sections[sec] for c in x["cites"] if c in kind}
    near = any(f.kind == "agent" and (f.data.get("max_pct") or 0) >= 80 for f in pack.facts)
    return {"limit_proximity": ("agent" in cited) if near else None,
            "time_window": bool(cited & {"span", "burst"}),
            "merchant_concentration": "merchant" in cited,
            "cross_alert_links": ("link" in cited) if any(f.kind == "link" for f in pack.facts) else None,
            "recommendation_with_reason": bool(note.recommendation and note.sections["reason"]),
            "next_steps": bool(note.sections["actions"])}


def pick(seeds=(301, 302, 303), per_seed=10):
    """Same selection method as v3: the reported case's counterpart (same seed and rule, regenerated data), then 10
    alerts per seed, round-robin over rules."""
    sh = generate(reference.SEED)
    out = [("reported (synth-v2)", sh, next(a for a in sh.alerts if str(a.rule) == "AML_TEAM_STRUCTURING"))]
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
        out += [(f"seed {s}", sh, a) for a in chosen]
    return out


def run_one(inv, client, judge_cache, label, a, by_id, reg, pool, queue, hist, truth):
    pack = build(a, by_id, reg, pool=pool, queue=queue, history=hist)
    note = inv.draft(a, by_id, reg, hist, pool=pool, queue=queue)
    facts = pack.by_id()
    head = f"Alert {a.alert_id}: rule {a.rule}, severity {a.severity}.\n[E1] {facts['E1'].text}"
    judged = []
    for sec in CLAIM_SECTIONS:
        for x in note.sections[sec]:
            cited = "\n".join(f"[{c}] {facts[c].text}" for c in x["cites"] if c in facts)
            content = f"{head}\n\nCited evidence lines:\n{cited}\n\nNote line ({sec}): {x['text']}"
            key = hashlib.sha256(json.dumps([JUDGE_MODEL, JUDGE_PROMPT, JUDGE_V, content]).encode()).hexdigest()
            p = judge_cache / f"{key}.json"
            if p.exists():
                v = json.loads(p.read_text())
            else:
                v = judge(client, content)
                if v.get("verdict") != "unparseable":
                    p.write_text(json.dumps(v))
            judged.append({"section": sec, **x, "judge": v.get("verdict"), "judge_reason": v.get("reason"),
                           "contradicts": v.get("contradicts_rule") is True})
    return {"label": label, "alert": a, "pack": pack, "note": note, "judged": judged, "truth": truth, "checks": checklist(note, pack)}


def summarise(rows) -> dict:
    tot, verdicts, rec, chk = Counter(), Counter(), Counter(), {c: Counter() for c in CHECKS}
    for r in rows:
        n = r["note"]
        tot["alerts"] += 1
        tot["notes_with_error"] += bool(n.error)
        tot["raw_lines"] += n.raw_lines
        tot["kept_lines"] += n.kept_lines
        tot["kept_claim_lines"] += sum(len(n.sections[s]) for s in CLAIM_SECTIONS)
        tot["cited_total"] += n.cited_total
        tot["cited_unknown"] += n.cited_unknown
        tot["notes_shown"] += bool(n.kept_lines)
        tot["notes_with_summary"] += bool(n.sections["summary"])
        for k, v in n.dropped.items():
            tot["dropped: " + k] += v
        for s in inv_mod.SECTIONS:
            tot[f"kept: {s}"] += len(n.sections[s])
        if r["truth"] is not None:
            rec[f"{'laundering' if r['truth']['laundering'] else 'benign'} -> {n.recommendation or 'none'}"] += 1
        for j in r["judged"]:
            verdicts[j["judge"] or "unparseable"] += 1
            verdicts["contradicts_rule"] += j["contradicts"]
        tot["notes_contradicting_rule"] += any(j["contradicts"] for j in r["judged"])
        for c, v in r["checks"].items():
            chk[c]["n/a" if v is None else ("pass" if v else "fail")] += 1
    judged = sum(verdicts[k] for k in ("supported", "partly", "unsupported", "unparseable"))
    return {"totals": dict(tot), "judge_verdicts_on_kept_claim_lines": dict(verdicts),
            "supported_rate": round(verdicts["supported"] / judged, 4) if judged else None,
            "citation_existence_rate": round(1 - tot["cited_unknown"] / tot["cited_total"], 4) if tot["cited_total"] else None,
            "usefulness_checklist": {c: dict(v) for c, v in chk.items()},
            "usefulness_pass_rate": {c: (round(v["pass"] / (v["pass"] + v["fail"]), 4) if v["pass"] + v["fail"] else None) for c, v in chk.items()},
            "recommendation_vs_truth": dict(rec)}


def main() -> None:
    load_env()
    client = GroqClient(default_model=MODEL)
    inv = Investigator(client, model=MODEL, cache_dir=CACHE / "investigator", min_interval_s=2.0)
    judge_cache = CACHE / "e3_judge"
    judge_cache.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, sh, a in pick():
        hist = None
        if a.subject_type == "agent":
            hist = [t for t in sh.txns if t.agent_id == a.subject_id and t.timestamp < a.raised_at - timedelta(hours=1)][-60:]
        rows.append(run_one(inv, client, judge_cache, label, a, sh.by_id, sh.registry, sh.pool,
                            frozenset(x.alert_id for x in sh.alerts), hist, sh.alert_truth(a)))
    fa, fby, freg, fpool, fq = reference.load()
    ref = run_one(inv, client, judge_cache, "reference (frozen, pre-fix data)", fa, fby, freg, fpool, fq, None, None)
    res = {"version": "E3 v4", "investigator_prompt": inv_mod.PROMPT_VERSION, "filter_version": inv_mod.FILTER_VERSION,
           "pack_version": ev_mod.PACK_VERSION, "data_version": DATA_VERSION, "investigator_model": MODEL, "judge_model": JUDGE_MODEL,
           "judge_version": JUDGE_V, "alerts": len(rows),
           "selection": "reported case's counterpart (seed 20261114, team structuring, regenerated data) + 10 alerts per seed 301-303",
           "main": summarise(rows), "reference_frozen": {**summarise([ref]), "alert_id": fa.alert_id, "note": ref["note"].as_dict(),
                                                        "judged": ref["judged"], "checks": ref["checks"]},
           "claim_check_thresholds": {"just_under_min_pct": inv_mod.NEAR_PCT, "burst_max_s": inv_mod.BURST_S, "short_period_max_s": inv_mod.SHORT_S},
           "earlier_results_unchanged": ["eval/results/e3_v1.json", "eval/results/e3_v2.json", "eval/results/e3_v3_prompt_only.json",
                                         "eval/results/e3_v3.json"],
           "note": "Figures shown with a note come from the evidence pack (code); the checker guarantees no model-written digits."}
    (ROOT / "eval/results/e3_v4.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ("main",)}, indent=1))
    print(json.dumps({k: v for k, v in res["reference_frozen"].items() if k not in ("judged",)}, indent=1, default=str))
    write_pack([ref] + [r for r in rows if r["note"].kept_lines][:9])


def write_pack(pack_rows) -> None:
    md = ["# E3 v4 hand-score pack (10 notes)", "",
          "Note 1 is the frozen reference case (A6c2d42955a, data before the whole-cent / ID-order fix). Notes 2–10 are the "
          "first nine v4 notes with kept lines (synth-v2 data). For each line mark Supported (Y/N) and Useful (Y/N/Partly) in "
          "handscore_v4.csv. SIMULATED money, synthetic data.", ""]
    with (ROOT / "eval/e3/handscore_v4.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["note", "alert_id", "line_no", "section", "line", "cites", "supported_Y_N", "useful_Y_N_Partly", "comment", "verdict_source"])
        for i, r in enumerate(pack_rows, 1):
            a, p, n = r["alert"], r["pack"], r["note"]
            md += [f"## Note {i}: {a.rule} (severity {a.severity}) · {r['label']}", "", "```",
                   "\n".join(f"[{x.id}] {x.text}" for x in p.facts), "```", ""]
            k = 0
            for sec in inv_mod.SECTIONS:
                for x in n.sections[sec]:
                    k += 1
                    facts = " | ".join(x["facts"])
                    md.append(f"{k}. **{sec}** — {x['text']}" + (f"  \n   _cites {', '.join(x['cites'])}: {facts}_" if x["cites"] else ""))
                    w.writerow([i, a.alert_id, k, sec, x["text"], " ".join(x["cites"]), "", "", "", ""])
            md += ["", f"Recommendation: **{n.recommendation}** · checklist: " +
                   ", ".join(f"{c} {'✓' if v else '✗'}" for c, v in r["checks"].items() if v is not None),
                   f"Dropped by the checker: {dict(n.dropped) or 'nothing'}", ""]
    (ROOT / "eval/e3/handscore_v4.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
