"""AI investigator v4: interprets a code-computed evidence pack for an AML alert. Stage 4.

The LLM proposes, code decides what is shown:
- Code builds the evidence pack (safespend.evidence): every figure, each line with an ID [E1], [E2], ...
- The model writes interpretation only, in a fixed template (Summary, Evidence, Open questions, Recommended
  actions, recommendation with reason), citing evidence IDs. It never types a number: the analyst sees each cited
  line's exact text, from the pack, next to the model's words.
- Code keeps a line only if it passes every check below. Everything dropped is counted, by reason, for E3.

Earlier versions (v1-v3: sentence notes citing transaction IDs) are in git history at commit 3c4b10d; their E3 scores
are kept in eval/results/e3_v1.json, e3_v2.json, e3_v3_prompt_only.json and e3_v3.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .aml.rules import Alert
from .evidence import MAX_LINKS, PACK_VERSION, Pack, build
from .money import fmt_usd
from .llm.client import LlmConfigError, LlmError, LlmRateLimited

PROMPT_VERSION = "v4-p4"  # v4-p4 (post-results): code writes the summary and the reason; the model writes why it matters, questions, actions
# v4-p3: v4-p3 (post-results): timing only through the pack's timing label
FILTER_VERSION = "v2.4-p4"  # v2.4-p4: "possible" is a hedge; checks apply to model lines only
# v2.3-p3: v2.3-p3: timing words outside the pack's label are dropped (replaces the burst/short-period checks)
# v2.2: v2.2 (after E3 v4 results): no excuse filter on open questions; negated phrases ("without a legitimate purpose") allowed
# v2.1: v2.1: normalise Unicode spaces/hyphens; agent names written as "Agent 08"; wider near/short phrases
# v2.0 claim checks: limit proximity >= 80%, burst <= 10 min, short period <= 24 h; doubts only as questions
NEAR_PCT = 80.0
MAX_PER_SECTION = 10
SECTIONS = ("summary", "why", "open_questions", "actions", "reason")  # summary and reason: code; the rest: model
MODEL_SECTIONS = {"why": "why_it_matters", "open_questions": "open_questions", "actions": "actions"}
TYPOLOGY = {"AML_STRUCTURING": "Structuring", "AML_TEAM_STRUCTURING": "Team structuring", "AML_VELOCITY_SPIKE": "Velocity spike",
            "AML_RAPID_FIRE": "Rapid-fire payments", "AML_ROUND_AMOUNTS": "Round-amount payments", "AML_LOOKALIKE_MERCHANT": "Look-alike merchant",
            "AML_NEW_MERCHANT_BURST": "New-merchant burst", "AML_DORMANT_THEN_ACTIVE": "Dormant agent suddenly active",
            "AML_FAN_IN": "Fan-in to one merchant", "AML_HIGH_RISK_CATEGORY": "Payments to a high-risk category"}

_EXCUSES = re.compile(r"\b(routine|normal|legitimate|innocent|innocuous|benign|typical|ordinary|expected|nothing unusual|"
                      r"business as usual|consistent with (?:normal|regular|routine|legitimate|business))\b", re.I)
_NEGATED = re.compile(r"\b(?:no|not|without|never|nor|lacks?|lacking|absence of|lack of|rather than)\b(?:\s+[\w'-]+){0,3}\s*$", re.I)


def excuses(text: str) -> bool:
    """True if the text excuses the flagged pattern. A negated excuse ("without a legitimate purpose", "not routine")
    argues FOR the alert, so it is allowed (v2.2). "nothing unusual" is always an excuse."""
    for m in _EXCUSES.finditer(text):
        if m.group(0).lower() == "nothing unusual" or not _NEGATED.search(text[:m.start()]):
            return True
    return False


_NUMBER_WORDS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
                           r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|hundred|thousand|dozen|half|twice)\b", re.I)
_NEAR = re.compile(r"\b(?:just|right|slightly|barely|narrowly)\s+(?:under|below|beneath|short of)\b|\b(?:close|near|nearly|up)\s+to\s+"
                   r"(?:the|its|their|each)?\s*(?:agent'?s?'?\s+)?(?:approval\s+)?(?:threshold|limit)s?\b|\bnear(?:ly)?[\s-]+(?:\w+\s+){0,3}"
                   r"(?:threshold|limit)|\bjust\s+short\s+of\b|\bapproach(?:es|ed|ing)?\s+(?:\w+\s+){0,3}(?:threshold|limit)", re.I)
_AGENT = re.compile(r"\bagent[\s_-]?\d{1,3}\b", re.I)
_UNI = str.maketrans({"\u202f": " ", "\u00a0": " ", "\u2009": " ", "\u2007": " ", "\u2011": "-", "\u2010": "-", "\u2013": "-",
                      "\u2014": "-", "\u2019": "'", "\u2018": "'"})
_TIMING = re.compile(r"\{\s*timing\s*:\s*(E\d{1,3})\s*\}", re.I)
_RULE_NAMES = re.compile(r"\b(?:new[- ]merchant bursts?|rapid[- ]fire|velocity spikes?)\b(?:\s+(?:rule|alert|pattern|detection))?", re.I)
_TIMEWORDS = re.compile(r"\b(?:seconds|minutes?|hours?|days?|weeks?|months?|overnight|short|shortly|brief|briefly|quick|quickly|rapid|rapidly|"
                        r"burst|bursts|flurry|swift|swiftly|fast|long|lengthy|extended|prolonged|gradual|gradually|slowly|succession|"
                        r"timeframe|time frame|time span|timespan|window|period|same day|soon|immediately|instantly|in a row|consecutive)\b", re.I)
_HEDGE = re.compile(r"\b(?:could|might|may|possible|possibly|perhaps|probably|likely|unlikely|appears? to|seems?|maybe|unclear|uncertain)\b", re.I)
_EID = re.compile(r"\[?\b(E\d{1,3})\b\]?")
_TID = re.compile(r"\bT\d{7}\b")
_AID = re.compile(r"\bA[0-9a-f]{10}\b")

SYSTEM_PROMPT = """You are an AML investigator reviewing an alert on payments made by AI agents (simulated money).
You are given an evidence pack computed by code from the ledger. Every line has an ID like [E3]. The pack is true.
Code already writes the note's summary (the pattern, counts, amounts, timing, share of threshold, merchant trust) and the
basis for the recommendation. You add only interpretation:
- why_it_matters: one or two sentences on why this pattern matters for money-laundering or fraud risk.
- open_questions: what the analyst should find out. Every doubt or innocent possibility goes here, and only here,
  phrased as a question ending in "?".
- actions: one to three concrete next steps for the analyst.
- recommendation: escalate, clear or more_info.

Rules:
- Cite evidence IDs (E1, E2, ...) for every why_it_matters sentence. Cite only IDs in the pack.
- Never type a number, as digits or words (no amounts, counts, dates, times, percentages, "two", "dozen", "half").
- Never describe timing in any way (no "short", "brief", "quick", "rapid", "burst", "period", "window", "minutes", "hours").
  Code states the timing.
- The rule explanation is true. Never dispute it or call the detected pattern routine, normal or legitimate.
- Outside open_questions, state only what the pack shows: no "could", "might", "may", "possible", "possibly", "appears".
- Recommend "clear" only if the pack shows a specific innocent reason; otherwise "escalate" or "more_info".

Reply with JSON only:
{"why_it_matters": [{"text": "...", "cites": ["E3"]}],
 "open_questions": [{"text": "...?", "cites": ["E5"]}],
 "actions": [{"text": "...", "cites": ["E7"]}],
 "recommendation": "escalate" | "clear" | "more_info"}"""


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def code_summary(pack: Pack) -> dict:
    """The summary's first sentence, written by code from the pack (p4)."""
    a = pack.alert
    by = {f.kind: f for f in pack.facts}
    ov, span = by["overview"], by["span"]
    agents = [f for f in pack.facts if f.kind == "agent"]
    merchants = [f for f in pack.facts if f.kind == "merchant"]
    pcts = [p for p in pack.pct.values()]
    n, na, nm = ov.data["payments"], ov.data["agents"], ov.data["merchants"]
    whose = "the agent's approval threshold" if na == 1 else "the agents' approval thresholds"
    lo, hi = (f"{min(pcts):.1f}", f"{max(pcts):.1f}") if pcts else ("", "")
    share = (f"at {lo}% of {whose}" if lo == hi else f"at {lo}%–{hi}% of {whose}") if pcts else ""
    when = f"on {span.text.split('First payment ')[1].split(',')[0]}" if n == 1 else span.data["label"]
    untrusted = [f for f in merchants if not f.data.get("trusted")]
    if nm == 1:
        m = merchants[0]
        trust = f"to {m.text.split(':')[0]}"
    elif len(untrusted) == nm:
        trust = "all to untrusted merchants"
    elif not untrusted:
        trust = "all to trusted merchants"
    else:
        trust = f"{len(untrusted)} of {nm} merchants untrusted"
    text = (f"{TYPOLOGY.get(str(a.rule), str(a.rule))}: {_plural(n, 'payment')} {'totalling' if n > 1 else 'of'} {fmt_usd(ov.data['total'])} "
            f"from {_plural(na, 'agent')} to {_plural(nm, 'merchant')}, {when}, {share}; {trust}.").replace(", ;", ";")
    cites = [ov.id, span.id] + [f.id for f in agents] + [f.id for f in merchants]
    return {"text": text, "cites": cites, "by": "code"}


def code_reason(pack: Pack) -> dict:
    """The basis for the recommendation, written by code from the rule and the pack (p4)."""
    a = pack.alert
    by = {f.kind: f for f in pack.facts}
    rule = by["rule"]
    parts = [f"{TYPOLOGY.get(str(a.rule), str(a.rule))} rule, severity {a.severity}: {a.explanation.rstrip('.')}."]
    cites = [rule.id]
    pcts = list(pack.pct.values())
    if pcts and min(pcts) >= NEAR_PCT:
        parts.append(f"Every payment is at {NEAR_PCT:.0f}% or more of its agent's approval threshold.")
        cites += [f.id for f in pack.facts if f.kind == "agent"]
    risky = [f for f in pack.facts if f.kind == "merchant" and not f.data.get("trusted")]
    if risky:
        parts.append(f"{_plural(len(risky), 'untrusted merchant')} involved.")
        cites += [f.id for f in risky]
    links = [f for f in pack.facts if f.kind == "link"]
    if links:
        inq = sum("in your queue" in f.text and "not in your queue" not in f.text for f in links)
        many = "at least " if len(links) >= MAX_LINKS else ""
        parts.append(f"Linked to {many}{_plural(len(links), 'other alert')} on the same untrusted merchants, owner or agents ({inq} of those in your queue).")
        cites += [f.id for f in links]
    return {"text": " ".join(parts), "cites": cites, "by": "code"}


@dataclass
class CaseNote:
    alert_id: str
    sections: dict[str, list[dict]]  # kept lines per section: {"text", "cites", "facts": [fact texts]}
    recommendation: str | None
    dropped: Counter = field(default_factory=Counter)  # reason -> count
    cited_total: int = 0
    cited_unknown: int = 0
    raw_lines: int = 0
    error: str | None = None
    latency_ms: float | None = None
    pack_facts: list[dict] = field(default_factory=list)

    @property
    def kept_lines(self) -> int:
        return sum(len(v) for v in self.sections.values())

    def as_dict(self) -> dict:
        return {"alert_id": self.alert_id, "version": PROMPT_VERSION, "sections": self.sections, "recommendation": self.recommendation,
                "dropped": dict(self.dropped), "cited_total": self.cited_total, "cited_unknown": self.cited_unknown,
                "raw_lines": self.raw_lines, "error": self.error, "pack": self.pack_facts}


def check_line(text: str, cites: list[str], section: str, pack: Pack, all_txns: dict, identifiers: set[str]) -> str | None:
    """Returns the drop reason, or None if the line may be shown."""
    facts = pack.by_id()
    text = text.translate(_UNI)
    for tok in _TIMING.findall(text):
        if tok not in facts:
            return "cites an ID not in the pack"
        if facts[tok].kind not in ("span", "burst"):
            return "timing label taken from a non-timing line"
        if tok not in cites:
            cites.append(tok)
    text = _TIMING.sub(" ", text)
    unknown = [c for c in cites if c not in facts]
    if unknown:
        return "cites an ID not in the pack"
    if not cites and section in ("summary", "evidence", "reason", "why"):
        return "no citation"
    scrub = _EID.sub("", text)
    scrub = _AGENT.sub("", _TID.sub("", _AID.sub("", scrub)))
    for ident in sorted(identifiers, key=len, reverse=True):
        scrub = scrub.replace(ident, "")
    if re.search(r"\d", scrub):
        return "contains a number"
    if _NUMBER_WORDS.search(scrub):
        return "contains a spelled-out number"
    if section != "open_questions" and excuses(scrub):
        return "argues against the alert's computed facts"
    if section == "open_questions":
        if _TIMEWORDS.search(_RULE_NAMES.sub(" ", scrub)):
            return "describes timing itself instead of using the pack's label"
        if not text.rstrip().endswith("?"):
            return "open question not phrased as a question"
        return None
    if _HEDGE.search(scrub):
        return "states a doubt outside open questions"
    cited_txns = {t for c in cites for t in facts[c].txns}
    if _NEAR.search(scrub):
        ps = [pack.pct.get(t) for t in cited_txns]
        if not ps or any(p is None or p < NEAR_PCT for p in ps):
            return "claims 'just under the threshold' without support"
    if _TIMEWORDS.search(_RULE_NAMES.sub(" ", scrub)):
        # pack p3: timing may only come from the pack's code-computed label, via {timing:E#}.
        return "describes timing itself instead of using the pack's label"
    return None


def _cites(item: dict) -> list[str]:
    c = item.get("cites") or ([item["cite"]] if item.get("cite") else [])
    out = [str(x).strip("[] ") for x in (c if isinstance(c, list) else [c])]
    out += [m for m in _EID.findall(str(item.get("text") or item.get("why") or "")) if m not in out]
    return out


def verify(alert_id: str, data: dict, pack: Pack, all_txns: dict, identifiers: set[str]) -> CaseNote:
    facts = pack.by_id()
    note = CaseNote(alert_id, {s: [] for s in SECTIONS}, None,
                    pack_facts=[{"id": f.id, "kind": f.kind, "text": f.text, "txns": list(f.txns)} for f in pack.facts])
    rec = str(data.get("recommendation") or "").strip().lower()
    note.recommendation = rec if rec in ("escalate", "clear", "more_info") else None
    for section, key in MODEL_SECTIONS.items():
        items = data.get(key) or []
        for i, item in enumerate(items if isinstance(items, list) else []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or item.get("why") or "").strip()
            if not text:
                continue
            note.raw_lines += 1
            if i >= MAX_PER_SECTION:
                note.dropped["over the section limit"] += 1
                continue
            cites = _cites(item)
            note.cited_total += len(cites)
            note.cited_unknown += sum(c not in facts for c in cites)
            why = check_line(text, cites, section, pack, all_txns, identifiers)
            if why:
                note.dropped[why] += 1
                continue
            clean = re.sub(r"\s*\[E\d{1,3}\]", "", text.translate(_UNI))
            clean = _TIMING.sub(lambda m: facts[m.group(1)].data.get("label", ""), clean)
            clean = re.sub(r"\s{2,}", " ", clean).strip()
            note.sections[section].append({"text": clean, "cites": cites, "facts": [facts[c].text for c in cites], "by": "model"})
    for section, fn in (("summary", code_summary), ("reason", code_reason)):
        line = fn(pack)
        note.sections[section].append({**line, "facts": [facts[c].text for c in line["cites"]]})
    return note


def identifiers_for(pack: Pack, registry) -> set[str]:
    names = set()
    for t in pack.rows:
        a, m = registry.agents.get(t.agent_id), registry.merchants.get(t.merchant_id)
        names |= {t.agent_id, a.owner_id if a else "", m.name if m else ""}
    names |= {registry.merchants[mid].name for mid in {t.merchant_id for t in pack.rows} if mid in registry.merchants}
    names |= {a.agent_id for a in registry.agents.values()} | {m.name for m in registry.merchants.values()}
    return {n for n in names if n}


class Investigator:
    def __init__(self, llm=None, *, model: str | None = None, cache_dir: Path | None = None, store: Any = None,
                 min_interval_s: float = 0.0, max_retries: int = 4) -> None:
        self.llm, self.model, self.cache_dir, self.store = llm, model, cache_dir, store
        self.min_interval_s, self.max_retries = min_interval_s, max_retries
        self._last = 0.0
        self.calls = self.cache_hits = 0
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def draft(self, alert: Alert, txns_by_id: dict, registry, history: list | None = None, *, pool=(), queue=frozenset()) -> CaseNote:
        pack = build(alert, txns_by_id, registry, pool=pool, queue=queue, history=history)
        ev, idents = pack.text(registry), identifiers_for(pack, registry)
        key = hashlib.sha256(json.dumps(["investigator", PROMPT_VERSION, PACK_VERSION, self.model, SYSTEM_PROMPT, ev]).encode()).hexdigest()
        path = self.cache_dir / f"{key}.json" if self.cache_dir else None
        raw = json.loads(path.read_text()) if path and path.exists() else (self.store.get(key) if self.store is not None else None)
        if raw is not None:
            self.cache_hits += 1
            return verify(alert.alert_id, raw, pack, txns_by_id, idents)
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ev}]
        resp, err = None, None
        for attempt in range(self.max_retries):
            wait = self.min_interval_s - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                resp = self.llm.complete(msgs, model=self.model, max_tokens=2500, temperature=0.0, json_mode=True)
                self.calls += 1
                break
            except LlmRateLimited:
                time.sleep(min(30, 5 * 2 ** attempt))
            except LlmConfigError as exc:
                err = str(exc)[:200]
                break
            except LlmError as exc:
                err = str(exc)[:200]
                time.sleep(1)
        fail = verify(alert.alert_id, {}, pack, txns_by_id, idents)  # code-written summary and basis still shown
        if resp is None:
            fail.error = err or "rate limited"
            return fail
        try:
            raw = json.loads(resp.text)
            if not isinstance(raw, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            fail.error, fail.latency_ms = "unparseable", resp.latency_ms
            return fail
        if path:
            path.write_text(json.dumps(raw))
        if self.store is not None:
            self.store.put(key, raw)
        note = verify(alert.alert_id, raw, pack, txns_by_id, idents)
        note.latency_ms = resp.latency_ms
        return note
