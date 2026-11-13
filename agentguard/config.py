"""Versioned policy configuration. Every decision records version and hash."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Mapping

from .models import sha256_hex


@dataclass(frozen=True)
class PolicyConfig:
    version: str = "policy-2026.11.10-1"
    # Owner-level (team) aggregation across all agents with the same owner.
    owner_daily_budgets: Mapping[str, int] = field(default_factory=dict)  # owner_id -> micro-dollars
    owner_max_payments_per_window: int | None = 50
    velocity_window_seconds: int = 60
    # Duplicate heuristics (backup to idempotency keys).
    duplicate_window_seconds: int = 5  # same agent+merchant+amount, no invoice ref
    invoice_duplicate_window_hours: int = 24  # same agent+merchant+amount+invoice ref
    # Approvals.
    approval_ttl_seconds: int = 900
    # Look-alike merchants.
    lookalike_max_distance: int = 2
    # Added after the red-team lock (Stage 3). Off by default = Stage 1 behaviour.
    price_check: bool = False  # block when the charged amount exceeds the quoted amount
    injection_near_limit: float = 0.8  # payments at >= this share of a limit count as borderline
    # Added after Stage 3 results (round 2). Off by default = Stage 1 behaviour.
    split_check: bool = False  # hold when same-merchant payments in the window add up to the approval threshold
    split_window_hours: int = 24  # trailing window, so splits cannot hide across midnight
    split_min_share: float = 0.1  # ignore payments under this share of the threshold (micropayments)
    lookalike_hold_min_trusted: int | None = None  # with at least this many trusted merchants, look-alikes hold

    @property
    def config_hash(self) -> str:
        data = asdict(self)
        data["owner_daily_budgets"] = dict(self.owner_daily_budgets)
        return sha256_hex(data)


@dataclass(frozen=True)
class BreakerConfig:
    spend_window_seconds: int = 600
    spend_limit: int = 200_000_000  # $200 SIMULATED across all agents in the window
    alert_window_seconds: int = 3600
    alert_limit: int = 10  # AML alerts in the window
