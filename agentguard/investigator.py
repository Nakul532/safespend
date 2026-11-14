"""AI investigator: drafts an evidence-cited case note for an AML alert. Stage 4.

The LLM proposes, code decides what is shown:
- The model sees the alert, its transactions and the agent's usual merchants, all computed by code.
- It must cite transaction IDs for every claim and write no numbers (amounts, counts and dates are shown
  by code next to the note, from the ledger).
- Code keeps a sentence only if it cites at least one ID, every cited ID is one the model was shown, and
  it contains no digit outside known identifiers. Everything dropped is counted, for E3.
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
from .llm.client import LlmConfigError, LlmError, LlmRateLimited
from .money import fmt_usd

PROMPT_VERSION = "v3"  # v2: may not argue against computed facts; v3: no number words either
FILTER_VERSION = "v1.2"  # v1.1: drop spelled-out numbers; v1.2 (hand review): drop sentences that excuse the flagged pattern
_EXCUSES = re.compile(r"\b(routine|normal|legitimate|innocent|innocuous|benign|typical|ordinary|expected|nothing unusual|"
                      r"business as usual|consistent with (?:normal|regular|routine|legitimate|business))\b", re.I)
_ID = re.compile(r"\bT\d{7}\b")
_NUMBER_WORDS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
                           r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|hundred|thousand|dozen)\b", re.I)

SYSTEM_PROMPT = """You are an AML investigator reviewing alerts on payments made by AI agents (simulated money).
Write a short case note for the analyst: three to five sentences on what the transactions show, why the pattern is or
is not suspicious, and what would explain it innocently. Then recommend one of: escalate, clear, more_info.

Rules:
- Every sentence must cite the transaction IDs it relies on, in square brackets, like [T0000123].
- Cite only IDs listed in the evidence. Do not invent facts that are not in the evidence.
- Do not write any numbers, as digits OR as words: no amounts, counts, dates, times or percentages, and no words such as
  "two", "three", "four", "dozen" or "hundred". Say "several", "a few", "multiple", "just under the threshold",
  "within minutes" instead. The analyst sees the exact figures next to your note.
- The rule explanation was computed by code from the ledger and is true. Never dispute it, and never describe the very
  pattern the rule detected as routine or normal: payments kept just under an approval threshold ARE the structuring red
  flag, a burst far above the agent's usual rate IS the velocity red flag, many agents paying one untrusted merchant IS the
  fan-in red flag. An innocent explanation may be offered only as something the analyst should verify, and only if the
  evidence supports it beyond the rule's own facts.
- Recommend "clear" only if the evidence shows a specific innocent reason; otherwise recommend "escalate" or "more_info".

Reply with JSON only:
{"sentences": [{"text": "...", "cites": ["T0000123", "..."]}], "recommendation": "escalate" | "clear" | "more_info"}"""


@dataclass
class CaseNote:
    alert_id: str
    sentences: list[dict]  # kept: {"text", "cites"}
    recommendation: str | None
    dropped: Counter = field(default_factory=Counter)  # reason -> count
    cited_total: int = 0
    cited_unknown: int = 0
    raw_sentences: int = 0
    error: str | None = None
    latency_ms: float | None = None

    def as_dict(self) -> dict:
        return {"alert_id": self.alert_id, "sentences": self.sentences, "recommendation": self.recommendation,
                "dropped": dict(self.dropped), "cited_total": self.cited_total, "cited_unknown": self.cited_unknown,
                "raw_sentences": self.raw_sentences, "error": self.error}


def evidence(alert: Alert, txns_by_id: dict, registry, history: list | None = None, max_rows: int = 25) -> tuple[str, set[str], set[str]]:
    """The evidence block the model sees, its allowed IDs, and identifier tokens that may contain digits."""
    rows = [txns_by_id[t] for t in alert.txn_ids][:max_rows]
    allowed = {t.txn_id for t in rows}
    names = set()
    lines = [f"Alert {alert.alert_id}: rule {alert.rule}, severity {alert.severity}, subject {alert.subject_type} {alert.subject_id}.",
             f"Rule explanation (computed by code): {alert.explanation}", "", "Transactions:"]
    for t in rows:
        a, m = registry.agents.get(t.agent_id), registry.merchants.get(t.merchant_id)
        names |= {t.agent_id, a.owner_id if a else "", m.name if m else ""}
        lines.append(f"{t.txn_id} | {t.timestamp:%Y-%m-%d %H:%M} | {t.agent_id} (team {a.owner_id if a else '?'}, approval threshold "
                     f"{fmt_usd(a.approval_threshold) if a else '?'}) | {m.name if m else t.merchant_id} ({m.category if m else '?'}, "
                     f"{'trusted' if m and m.trusted else 'untrusted'}) | {fmt_usd(t.amount)}")
    if history:
        usual = Counter(registry.merchants[t.merchant_id].name for t in history if t.merchant_id in registry.merchants)
        lines += ["", "Merchants this agent usually pays (from its history): " + ", ".join(n for n, _ in usual.most_common(4))]
    return "\n".join(lines), allowed, {n for n in names if n}


def verify(alert_id: str, data: dict, allowed: set[str], identifiers: set[str]) -> CaseNote:
    note = CaseNote(alert_id, [], None)
    rec = str(data.get("recommendation") or "").strip().lower()
    note.recommendation = rec if rec in ("escalate", "clear", "more_info") else None
    for s in data.get("sentences") or []:
        note.raw_sentences += 1
        text = str((s or {}).get("text") or "").strip()
        cites = {c for c in (s.get("cites") or []) if isinstance(c, str)} | set(_ID.findall(text))
        note.cited_total += len(cites)
        unknown = cites - allowed
        note.cited_unknown += len(unknown)
        scrub = _ID.sub("", text)
        for ident in sorted(identifiers, key=len, reverse=True):
            scrub = scrub.replace(ident, "")
        if not text:
            continue
        if unknown:
            note.dropped["cites an ID it was not shown"] += 1
        elif not cites:
            note.dropped["no citation"] += 1
        elif re.search(r"\d", scrub):
            note.dropped["contains a number"] += 1
        elif _NUMBER_WORDS.search(scrub):
            note.dropped["contains a spelled-out number"] += 1
        elif _EXCUSES.search(scrub):
            # The rule's facts are computed by code and true; the model may not argue them away.
            note.dropped["argues against the alert's computed facts"] += 1
        else:
            note.sentences.append({"text": text, "cites": sorted(cites)})
    return note


class Investigator:
    def __init__(self, llm=None, *, model: str | None = None, cache_dir: Path | None = None, store: Any = None,
                 min_interval_s: float = 0.0, max_retries: int = 4) -> None:
        self.llm, self.model, self.cache_dir, self.store = llm, model, cache_dir, store
        self.min_interval_s, self.max_retries = min_interval_s, max_retries
        self._last = 0.0
        self.calls = self.cache_hits = 0
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def draft(self, alert: Alert, txns_by_id: dict, registry, history: list | None = None) -> CaseNote:
        ev, allowed, idents = evidence(alert, txns_by_id, registry, history)
        key = hashlib.sha256(json.dumps(["investigator", PROMPT_VERSION, self.model, ev]).encode()).hexdigest()
        path = self.cache_dir / f"{key}.json" if self.cache_dir else None
        raw = json.loads(path.read_text()) if path and path.exists() else (self.store.get(key) if self.store is not None else None)
        if raw is not None:
            self.cache_hits += 1
            return verify(alert.alert_id, raw, allowed, idents)
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ev}]
        resp, err = None, None
        for attempt in range(self.max_retries):
            wait = self.min_interval_s - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                resp = self.llm.complete(msgs, model=self.model, max_tokens=1500, temperature=0.0, json_mode=True)
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
        if resp is None:
            return CaseNote(alert.alert_id, [], None, error=err or "rate limited")
        try:
            raw = json.loads(resp.text)
        except json.JSONDecodeError:
            return CaseNote(alert.alert_id, [], None, error="unparseable", latency_ms=resp.latency_ms)
        if path:
            path.write_text(json.dumps(raw))
        if self.store is not None:
            self.store.put(key, raw)
        note = verify(alert.alert_id, raw, allowed, idents)
        note.latency_ms = resp.latency_ms
        return note
