"""Recurring-commitment and stored-credential holds. ADDED AFTER LOCK (Stage 4 game, level 4).

Minimal by design. A payment that creates a future commitment (subscription, a trial that converts,
auto top-up) or stores a payment credential with the merchant is held for a human. Commitments come
from two places: what the agent declares on the request, and deterministic keyword patterns in the
content the agent read (so a $0 trial that silently converts is still seen).

Known gaps (stated on screen):
- After approval, later merchant-initiated charges on a stored credential do not pass through AgentGuard
  unless the payment rails route them here; nothing here intercepts them.
- Future liabilities are recorded at sign-up only; there is no subscription ledger, renewal tracking or
  cancellation.
- Term detection is English keyword patterns over text; terms in images or PDFs, or reworded, are missed.
- A worst-case amount is computed only when the terms give an amount and a period.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .models import Commitment

_PATTERNS: dict[str, re.Pattern] = {
    "trial_conversion": re.compile(
        r"free trial|trial (period )?(ends|converts|expires)|after (the|your) trial|"
        r"\$\s?0(\.00)? (today|now)|then \$\s?\d[\d,]*(\.\d+)?\s*(/|per|a|every)\s*(month|mo|year|yr|week|wk)", re.I),
    "recurring": re.compile(
        r"\b(per|/|a|every)\s*(month|mo|year|yr|week|wk)\b|\bmonthly\b|\bsubscription\b|auto-?renew|"
        r"renews automatically|billed (monthly|annually|yearly|weekly)", re.I),
    "auto_topup": re.compile(
        r"auto[- ]?(top[- ]?up|recharge|reload|refill)|automatic(ally)? (top[- ]?up|reload|recharge|refill)|"
        r"(reload|top[- ]?up|recharge)s? when (your )?balance", re.I),
}
_CREDENTIAL = re.compile(
    r"save (this|your|my) (card|payment method)|card on file|keep (your|my) card|store (your|my) (card|payment)|"
    r"remember (this|my) card|pre-?ticked|checked by default|\[x\]|☑|✅ ?save", re.I)


@dataclass(frozen=True)
class TermsFound:
    kinds: tuple[str, ...]  # commitment kinds detected in the text
    credential: bool
    snippets: tuple[str, ...]


def _texts(context: Mapping[str, Any] | None):
    for v in (context or {}).values():
        if isinstance(v, str):
            yield v
        elif isinstance(v, (list, tuple)):
            yield from (x for x in v if isinstance(x, str))


def detect_terms(context: Mapping[str, Any] | None) -> TermsFound:
    kinds, snippets, cred = [], [], False
    for text in _texts(context):
        for kind, pat in _PATTERNS.items():
            m = pat.search(text)
            if m and kind not in kinds:
                kinds.append(kind)
                snippets.append(m.group(0))
        m = _CREDENTIAL.search(text)
        if m:
            cred = True
            snippets.append(m.group(0))
    return TermsFound(tuple(kinds), cred, tuple(snippets))


def worst_case(c: Commitment, horizon_days: int) -> int | None:
    """Most this commitment can charge over the horizon, in micro-dollars; None = no stated limit."""
    if c.kind == "auto_topup" or c.amount_per_period is None or not c.period_days:
        return None
    return c.amount_per_period * math.ceil(horizon_days / c.period_days)
