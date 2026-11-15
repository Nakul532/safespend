"""Circuit breaker: pauses all agent spending when spend or alert volume spikes.

Resuming needs a registered human approver who does not own any agent
involved in the trip. Every trip, resume and refused resume is logged.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from .audit import AuditLog, EventType
from .clock import Clock
from .config import BreakerConfig
from .ledger import Ledger
from .money import fmt_usd
from .registry import Registry


class BreakerError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self, clock: Clock, config: BreakerConfig, registry: Registry, audit: AuditLog, policy_version: str
    ) -> None:
        self._clock = clock
        self._config = config
        self._registry = registry
        self._audit = audit
        self._policy_version = policy_version
        self.is_open = False
        self.trip_reason: str | None = None
        self.trip_agents: frozenset[str] = frozenset()
        self._count_from: datetime | None = None  # ignore activity before the last resume

    def _since(self, seconds: int) -> datetime:
        start = self._clock.now() - timedelta(seconds=seconds)
        if self._count_from is not None and self._count_from > start:
            return self._count_from
        return start

    def _counts(self, ts: datetime) -> bool:
        """Activity at or before the last resume was already reviewed by a human."""
        return self._count_from is None or ts > self._count_from

    def trip(self, reason: str, agent_ids: Iterable[str], facts: dict | None = None) -> None:
        if self.is_open:
            return
        self.is_open = True
        self.trip_reason = reason
        self.trip_agents = frozenset(agent_ids)
        owners = sorted({self._registry.agents[a].owner_id for a in self.trip_agents if a in self._registry.agents})
        self._audit.append(
            EventType.BREAKER_TRIPPED,
            {"reason": reason, "agents": sorted(self.trip_agents), "owners": owners, **(facts or {})},
            self._policy_version,
        )

    def evaluate_spend(self, ledger: Ledger) -> None:
        if self.is_open:
            return
        window = [t for t in ledger.payments(since=self._since(self._config.spend_window_seconds)) if self._counts(t.timestamp)]
        total = sum(t.amount for t in window)
        if total > self._config.spend_limit:
            self.trip(
                f"spend {fmt_usd(total)} in {self._config.spend_window_seconds}s exceeded {fmt_usd(self._config.spend_limit)}",
                {t.agent_id for t in window},
                {"spend_micros": total, "limit_micros": self._config.spend_limit},
            )

    def evaluate_alerts(self, alerts: Iterable, ledger: Ledger) -> None:
        """Trip if too many AML alerts were raised inside the alert window."""
        if self.is_open:
            return
        since = self._since(self._config.alert_window_seconds)
        recent = [a for a in alerts if a.raised_at >= since and self._counts(a.raised_at)]
        if len(recent) >= self._config.alert_limit:
            agents: set[str] = set()
            for a in recent:
                for tid in a.txn_ids:
                    t = ledger.get(tid)
                    if t is not None:
                        agents.add(t.agent_id)
            self.trip(
                f"{len(recent)} AML alerts in {self._config.alert_window_seconds}s reached the limit of {self._config.alert_limit}",
                agents,
                {"alert_count": len(recent), "alert_limit": self._config.alert_limit},
            )

    def resume(self, approver_id: str) -> None:
        if not self.is_open:
            raise BreakerError("circuit breaker is not open")
        why: str | None = None
        involved_owners = {self._registry.agents[a].owner_id for a in self.trip_agents if a in self._registry.agents}
        if approver_id in self._registry.agents:
            why = "agents cannot resume spending"
        elif approver_id not in self._registry.approvers:
            why = "not a registered human approver"
        elif approver_id in involved_owners:
            why = "owner of an agent involved in the trip cannot resume spending (four-eyes)"
        if why:
            self._audit.append(
                EventType.BREAKER_RESUME_REFUSED, {"approver_id": approver_id, "reason": why}, self._policy_version
            )
            raise BreakerError(why)
        self._audit.append(
            EventType.BREAKER_RESUMED,
            {"approver_id": approver_id, "trip_reason": self.trip_reason, "agents": sorted(self.trip_agents)},
            self._policy_version,
        )
        self.is_open = False
        self.trip_reason = None
        self.trip_agents = frozenset()
        self._count_from = self._clock.now()
