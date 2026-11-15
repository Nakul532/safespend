"""AI investigator v4: interprets a code-computed evidence pack for an AML alert. Stage 4.

The LLM proposes, code decides what is shown:
- Code builds the evidence pack (agentguard.evidence): every figure, each line with an ID [E1], [E2], ...
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
from .evidence import PACK_VERSION, Pack, build
from .llm.client import LlmConfigError, LlmError, LlmRateLimited

PROMPT_VERSION = "v4"
FILTER_VERSION = "v2.1"  # v2.1: normalise Unicode spaces/hyphens; agent names written as "Agent 08"; wider near/short phrases
# v2.0 claim checks: limit proximity >= 80%, burst <= 10 min, short period <= 24 h; doubts only as questions
NEAR_PCT, BURST_S, SHORT_S = 80.0, 600, 86400
MAX_PER_SECTION = 10
SECTIONS = ("summary", "evidence", "open_questions", "actions", "reason")

_EXCUSES = re.compile(r"\b(routine|normal|legitimate|innocent|innocuous|benign|typical|ordinary|expected|nothing unusual|"
                      r"business as usual|consistent with (?:normal|regular|routine|legitimate|business))\b", re.I)
_NUMBER_WORDS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
                           r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|hundred|thousand|dozen|half|twice)\b", re.I)
_NEAR = re.compile(r"\b(?:just|right|slightly|barely|narrowly)\s+(?:under|below|beneath|short of)\b|\b(?:close|near|nearly|up)\s+to\s+"
                   r"(?:the|its|their|each)?\s*(?:agent'?s?'?\s+)?(?:approval\s+)?(?:threshold|limit)s?\b|\bnear(?:ly)?[\s-]+(?:\w+\s+){0,3}"
                   r"(?:threshold|limit)|\bjust\s+short\s+of\b|\bapproach(?:es|ed|ing)?\s+(?:\w+\s+){0,3}(?:threshold|limit)", re.I)
_BURST = re.compile(r"\b(?:burst|bursts|rapid|rapidly|rapid[- ]fire|flurry|quick succession|in quick|within minutes|within seconds|"
                    r"minutes apart|seconds apart)\b", re.I)
_SHORT = re.compile(r"\b(?:short[\s-]+(?:period|window|time|timeframe|time frame|span|interval|stretch)|brief (?:period|window|span)|quickly|in quick order|within hours|same day|over a day)\b", re.I)
_AGENT = re.compile(r"\bagent[\s_-]?\d{1,3}\b", re.I)
_UNI = str.maketrans({"\u202f": " ", "\u00a0": " ", "\u2009": " ", "\u2007": " ", "\u2011": "-", "\u2010": "-", "\u2013": "-",
                      "\u2014": "-", "\u2019": "'", "\u2018": "'"})
_HEDGE = re.compile(r"\b(?:could|might|may|possibly|perhaps|probably|likely|unlikely|appears? to|seems?|maybe|unclear|uncertain)\b", re.I)
_EID = re.compile(r"\[?\b(E\d{1,3})\b\]?")
_TID = re.compile(r"\bT\d{7}\b")
_AID = re.compile(r"\bA[0-9a-f]{10}\b")

SYSTEM_PROMPT = """You are an AML investigator reviewing an alert on payments made by AI agents (simulated money).
You are given an evidence pack computed by code from the ledger. Every line has an ID like [E3]. The pack is true.

Write a case note in this fixed template. Interpret the evidence; do not restate figures.
- summary: one or two sentences on what the pattern is and why it matters.
- evidence: the pack lines that matter most, each with one clause on why it matters.
- open_questions: what the analyst should find out. Every doubt or innocent possibility goes here, and only here,
  phrased as a question ending in "?".
- actions: one to three concrete next steps for the analyst.
- recommendation: escalate, clear or more_info, with a one-sentence reason.

Rules:
- Cite evidence IDs (E1, E2, ...) for every summary sentence, evidence item and the reason. Cite only IDs in the pack.
- Never type a number, as digits or words (no amounts, counts, dates, times, percentages, "two", "dozen", "half").
  The analyst sees each cited line's exact figures next to your words. Say "several", "most", "all" instead.
- Say "just under the threshold" only for payments the pack shows at or above eighty percent of the threshold.
  Say "burst" or "within minutes" only for a stretch the pack shows within ten minutes; "short period" only within a day.
- The rule explanation is true. Never dispute it or call the detected pattern routine, normal or legitimate.
- Outside open_questions, state only what the pack shows: no "could", "might", "may", "possibly", "appears".
- Recommend "clear" only if the pack shows a specific innocent reason; otherwise "escalate" or "more_info".

Reply with JSON only:
{"summary": [{"text": "...", "cites": ["E1"]}],
 "evidence": [{"cite": "E3", "why": "..."}],
 "open_questions": [{"text": "...?", "cites": ["E5"]}],
 "actions": [{"text": "...", "cites": ["E7"]}],
 "recommendation": "escalate" | "clear" | "more_info",
 "reason": {"text": "...", "cites": ["E2"]}}"""


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
    unknown = [c for c in cites if c not in facts]
    if unknown:
        return "cites an ID not in the pack"
    if not cites and section in ("summary", "evidence", "reason"):
        return "no citation"
    scrub = _EID.sub("", text)
    scrub = _AGENT.sub("", _TID.sub("", _AID.sub("", scrub)))
    for ident in sorted(identifiers, key=len, reverse=True):
        scrub = scrub.replace(ident, "")
    if re.search(r"\d", scrub):
        return "contains a number"
    if _NUMBER_WORDS.search(scrub):
        return "contains a spelled-out number"
    if _EXCUSES.search(scrub):
        return "argues against the alert's computed facts"
    if section == "open_questions":
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
    if _BURST.search(scrub):
        times = sorted(all_txns[t].timestamp for t in cited_txns if t in all_txns)
        if len(times) < 3 or (times[-1] - times[0]).total_seconds() > BURST_S:
            return "claims a burst without support"
    if _SHORT.search(scrub):
        times = sorted(all_txns[t].timestamp for t in cited_txns if t in all_txns)
        if len(times) < 2 or (times[-1] - times[0]).total_seconds() > SHORT_S:
            return "claims a short period without support"
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
    for section in SECTIONS:
        items = data.get(section) or []
        if section == "reason":
            items = [items] if isinstance(items, dict) else []
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
            clean = re.sub(r"\s*\[E\d{1,3}\]", "", text.translate(_UNI)).strip()
            note.sections[section].append({"text": clean, "cites": cites, "facts": [facts[c].text for c in cites]})
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
        fail = CaseNote(alert.alert_id, {s: [] for s in SECTIONS}, None,
                        pack_facts=[{"id": f.id, "kind": f.kind, "text": f.text, "txns": list(f.txns)} for f in pack.facts])
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
