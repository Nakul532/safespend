"""AML rules over settled agent payments.

Ported from ComplianceGuard's rule engine, with bank-cash thresholds
(e.g. $9,000-$9,999) replaced by limits relative to each agent's own
approval threshold. Two rules are new for agents: look-alike merchants and
new-merchant bursts. Team structuring aggregates across all agents with the
same owner.

Every rule takes settled payments sorted by time and returns Alerts. Each
alert's facts and explanation are computed by code from the ledger.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Sequence

from ..ledger import LedgerTxn
from ..lookalike import find_lookalike
from ..models import sha256_hex
from ..money import fmt_usd, usd
from ..reason_codes import ReasonCode
from ..registry import Registry

HIGH_RISK_CATEGORIES = frozenset({"gift_cards", "crypto_exchange", "money_transfer", "gambling", "prepaid_cards"})


@dataclass(frozen=True)
class AmlConfig:
    # Structuring: payments just under the approval threshold.
    structuring_window_hours: int = 24
    structuring_band_low: float = 0.8  # fraction of the approval threshold
    structuring_min_count: int = 3
    # Velocity spike vs. the agent's own baseline.
    spike_window_minutes: int = 60
    spike_baseline_days: int = 7
    spike_multiplier: float = 5.0
    spike_min_count: int = 10
    # Rapid-fire: many payments in a very short window.
    rapid_fire_window_seconds: int = 60
    rapid_fire_min_count: int = 15
    # Round amounts.
    round_unit: int = usd(10)
    round_min_count: int = 3
    round_window_hours: int = 24
    # New-merchant burst.
    new_merchant_window_hours: int = 24
    new_merchant_min_count: int = 3
    # Dormant then active.
    dormant_days: int = 14
    dormant_burst_count: int = 3
    dormant_burst_hours: int = 24
    # Fan-in: many agents paying one untrusted merchant.
    fan_in_window_hours: int = 24
    fan_in_min_agents: int = 3
    # Look-alike merchants.
    lookalike_max_distance: int = 2


@dataclass(frozen=True)
class Alert:
    alert_id: str
    rule: ReasonCode
    severity: int  # 1-10
    subject_type: str  # agent | owner | merchant
    subject_id: str
    txn_ids: tuple[str, ...]
    raised_at: datetime  # time of the payment that completed the pattern
    explanation: str
    facts: dict[str, Any] = field(default_factory=dict)


def _make_alert(rule: ReasonCode, severity: int, subject_type: str, subject_id: str,
                txns: Sequence[LedgerTxn], explanation: str, facts: dict[str, Any]) -> Alert:
    ids = tuple(sorted({t.txn_id for t in txns}))
    # Identity = rule + subject + first payment, so an episode that grows keeps its id.
    first = min(txns, key=lambda t: (t.timestamp, t.txn_id)).txn_id
    aid = "A" + sha256_hex({"rule": rule, "subject": subject_id, "first": first})[:10]
    return Alert(aid, rule, severity, subject_type, subject_id, ids, max(t.timestamp for t in txns), explanation, facts)


def _group(txns: Iterable[LedgerTxn], key: Callable[[LedgerTxn], str | None]) -> dict[str, list[LedgerTxn]]:
    out: dict[str, list[LedgerTxn]] = defaultdict(list)
    for t in txns:
        k = key(t)
        if k is not None:
            out[k].append(t)
    for v in out.values():
        v.sort(key=lambda t: (t.timestamp, t.txn_id))
    return out


def _episodes(txns: list[LedgerTxn], window: timedelta, hit: Callable[[list[LedgerTxn]], bool]) -> list[list[LedgerTxn]]:
    """Slide a window ending at each payment; merge overlapping windows that hit into one episode."""
    episodes: list[list[LedgerTxn]] = []
    start = 0
    for end in range(len(txns)):
        while txns[end].timestamp - txns[start].timestamp > window:
            start += 1
        win = txns[start:end + 1]
        if hit(win):
            if episodes and {t.txn_id for t in episodes[-1]} & {t.txn_id for t in win}:
                merged = {t.txn_id: t for t in episodes[-1] + win}
                episodes[-1] = sorted(merged.values(), key=lambda t: (t.timestamp, t.txn_id))
            else:
                episodes.append(list(win))
    return episodes


# -- rules --------------------------------------------------------------------

def _in_band(t: LedgerTxn, reg: Registry, cfg: AmlConfig) -> bool:
    agent = reg.agents.get(t.agent_id)
    if agent is None:
        return False
    thr = agent.approval_threshold
    return thr * cfg.structuring_band_low <= t.amount < thr


def structuring(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    """One agent splits spending into payments just under its approval threshold."""
    alerts = []
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        band = [t for t in ts if _in_band(t, reg, cfg)]
        thr = reg.agents[agent_id].approval_threshold
        for ep in _episodes(band, timedelta(hours=cfg.structuring_window_hours),
                            lambda w: len(w) >= cfg.structuring_min_count and sum(t.amount for t in w) >= thr):
            total = sum(t.amount for t in ep)
            alerts.append(_make_alert(
                ReasonCode.AML_STRUCTURING, 8, "agent", agent_id, ep,
                f"{len(ep)} payments each just under the {fmt_usd(thr)} approval threshold, totalling {fmt_usd(total)}.",
                {"count": len(ep), "total_micros": total, "threshold_micros": thr},
            ))
    return alerts


def team_structuring(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    """Several agents with the same owner each stay under their thresholds; together they structure."""
    alerts = []
    for owner_id, ts in _group(txns, lambda t: t.owner_id).items():
        band = [t for t in ts if _in_band(t, reg, cfg)]

        def hit(w: list[LedgerTxn]) -> bool:
            agents = {t.agent_id for t in w}
            max_thr = max(reg.agents[a].approval_threshold for a in agents)
            return len(agents) >= 2 and len(w) >= cfg.structuring_min_count and sum(t.amount for t in w) >= max_thr

        for ep in _episodes(band, timedelta(hours=cfg.structuring_window_hours), hit):
            agents = sorted({t.agent_id for t in ep})
            total = sum(t.amount for t in ep)
            alerts.append(_make_alert(
                ReasonCode.AML_TEAM_STRUCTURING, 8, "owner", owner_id, ep,
                f"{len(ep)} payments from {len(agents)} agents of one owner, each just under its approval threshold, totalling {fmt_usd(total)}.",
                {"count": len(ep), "agents": agents, "total_micros": total},
            ))
    return alerts


def velocity_spike(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    """An agent's hourly payment count jumps far above its own recent baseline."""
    alerts = []
    window = timedelta(minutes=cfg.spike_window_minutes)
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        first = ts[0].timestamp

        def hit(w: list[LedgerTxn]) -> bool:
            w_start = w[-1].timestamp - window
            base_start = w_start - timedelta(days=cfg.spike_baseline_days)
            if first > w_start - timedelta(days=1):
                return False  # needs at least a day of history before the window
            base_from = max(base_start, first)
            base = sum(1 for t in ts if base_from <= t.timestamp < w_start)
            hours = max((w_start - base_from) / timedelta(hours=1), 1.0)
            per_window = base / hours * (window / timedelta(hours=1))
            return len(w) >= max(cfg.spike_min_count, cfg.spike_multiplier * per_window)

        for ep in _episodes(ts, window, hit):
            alerts.append(_make_alert(
                ReasonCode.AML_VELOCITY_SPIKE, 6, "agent", agent_id, ep,
                f"{len(ep)} payments in a burst, far above this agent's usual rate.",
                {"count": len(ep)},
            ))
    return alerts


def rapid_fire(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    alerts = []
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        for ep in _episodes(ts, timedelta(seconds=cfg.rapid_fire_window_seconds),
                            lambda w: len(w) >= cfg.rapid_fire_min_count):
            alerts.append(_make_alert(
                ReasonCode.AML_RAPID_FIRE, 5, "agent", agent_id, ep,
                f"{len(ep)} payments with at least {cfg.rapid_fire_min_count} inside {cfg.rapid_fire_window_seconds}s.",
                {"count": len(ep)},
            ))
    return alerts


def round_amounts(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    alerts = []
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        rounds = [t for t in ts if t.amount >= cfg.round_unit and t.amount % cfg.round_unit == 0]
        for ep in _episodes(rounds, timedelta(hours=cfg.round_window_hours), lambda w: len(w) >= cfg.round_min_count):
            alerts.append(_make_alert(
                ReasonCode.AML_ROUND_AMOUNTS, 4, "agent", agent_id, ep,
                f"{len(ep)} payments in exact multiples of {fmt_usd(cfg.round_unit)}.",
                {"count": len(ep), "unit_micros": cfg.round_unit},
            ))
    return alerts


def lookalike_merchants(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    alerts = []
    trusted = reg.trusted_merchants()
    for merchant_id, ts in _group(txns, lambda t: t.merchant_id).items():
        m = reg.merchants.get(merchant_id)
        if m is None:
            continue
        match = find_lookalike(m, trusted, cfg.lookalike_max_distance)
        if match is None:
            continue
        total = sum(t.amount for t in ts)
        alerts.append(_make_alert(
            ReasonCode.AML_LOOKALIKE_MERCHANT, 9, "merchant", merchant_id, ts,
            f"Paid '{m.name}', which resembles trusted merchant '{match.resembles_name}': {len(ts)} payments, {fmt_usd(total)}.",
            {"count": len(ts), "total_micros": total, "resembles": match.resembles_id, "distance": match.distance},
        ))
    return alerts


def new_merchant_burst(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    """An agent with history suddenly pays several merchants it has never paid before."""
    alerts = []
    window = timedelta(hours=cfg.new_merchant_window_hours)
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        seen: set[str] = set()
        firsts: list[LedgerTxn] = []
        for t in ts:
            if t.merchant_id not in seen:
                seen.add(t.merchant_id)
                firsts.append(t)
        established = firsts[0].timestamp  # the agent's first ever payment

        def hit(w: list[LedgerTxn]) -> bool:
            return len(w) >= cfg.new_merchant_min_count and w[0].timestamp - established > window

        for ep in _episodes(firsts[1:], window, hit):
            alerts.append(_make_alert(
                ReasonCode.AML_NEW_MERCHANT_BURST, 6, "agent", agent_id, ep,
                f"{len(ep)} first-time merchants inside {cfg.new_merchant_window_hours}h.",
                {"count": len(ep), "merchants": sorted({t.merchant_id for t in ep})},
            ))
    return alerts


def dormant_then_active(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    alerts = []
    gap = timedelta(days=cfg.dormant_days)
    burst = timedelta(hours=cfg.dormant_burst_hours)
    for agent_id, ts in _group(txns, lambda t: t.agent_id).items():
        for i in range(1, len(ts)):
            idle = ts[i].timestamp - ts[i - 1].timestamp
            if idle < gap:
                continue
            after = [t for t in ts[i:] if t.timestamp - ts[i].timestamp <= burst]
            if len(after) >= cfg.dormant_burst_count:
                alerts.append(_make_alert(
                    ReasonCode.AML_DORMANT_THEN_ACTIVE, 5, "agent", agent_id, after,
                    f"Idle for {idle.days} days, then {len(after)} payments within {cfg.dormant_burst_hours}h.",
                    {"idle_days": idle.days, "count": len(after)},
                ))
    return alerts


def fan_in(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    """Many different agents pay one untrusted merchant in a short time."""
    alerts = []
    for merchant_id, ts in _group(txns, lambda t: t.merchant_id).items():
        m = reg.merchants.get(merchant_id)
        if m is None or m.trusted:
            continue
        for ep in _episodes(ts, timedelta(hours=cfg.fan_in_window_hours),
                            lambda w: len({t.agent_id for t in w}) >= cfg.fan_in_min_agents):
            agents = sorted({t.agent_id for t in ep})
            alerts.append(_make_alert(
                ReasonCode.AML_FAN_IN, 7, "merchant", merchant_id, ep,
                f"{len(agents)} different agents paid untrusted merchant '{m.name}' within {cfg.fan_in_window_hours}h.",
                {"agents": agents, "count": len(ep)},
            ))
    return alerts


def high_risk_category(txns: list[LedgerTxn], reg: Registry, cfg: AmlConfig) -> list[Alert]:
    alerts = []
    for merchant_id, ts in _group(txns, lambda t: t.merchant_id).items():
        m = reg.merchants.get(merchant_id)
        if m is None or m.category not in HIGH_RISK_CATEGORIES:
            continue
        total = sum(t.amount for t in ts)
        alerts.append(_make_alert(
            ReasonCode.AML_HIGH_RISK_CATEGORY, 6, "merchant", merchant_id, ts,
            f"{len(ts)} payments, {fmt_usd(total)}, to a merchant in high-risk category '{m.category}'.",
            {"count": len(ts), "total_micros": total, "category": m.category},
        ))
    return alerts


ALL_RULES: tuple[Callable[[list[LedgerTxn], Registry, AmlConfig], list[Alert]], ...] = (
    structuring,
    team_structuring,
    velocity_spike,
    rapid_fire,
    round_amounts,
    lookalike_merchants,
    new_merchant_burst,
    dormant_then_active,
    fan_in,
    high_risk_category,
)
