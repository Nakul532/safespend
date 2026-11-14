"""Seeded synthetic agent-payment data for Analyst shift and E3. SIMULATED; no real data.

Normal agent purchasing over 21 days, benign activity that looks suspicious (busy bursts, round SaaS
seats, a popular new tool many agents adopt, onboarding new vendors), and planted laundering patterns in
the last 7 days. The planted patterns are the labels. Alerts come from the real AML rules
(agentguard.aml.rules) run over the ledger; nothing is hand-placed in the queue.

Some planted patterns are designed to evade the rules (slow drip under the structuring band, chain
layering), so a shift always has laundering that no alert shows.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .aml.monitor import AmlMonitor
from .aml.rules import Alert
from .ledger import LedgerTxn, Posting, TxnKind
from .models import Agent, Merchant
from .money import usd
from .registry import Registry

DAYS = 21
PLANT_DAYS = 7
START = datetime(2026, 10, 26, tzinfo=timezone.utc)

TRUSTED = [("DataLoom", "data"), ("SkyFeed Data", "data"), ("CoreCloud", "compute"), ("Gridline Compute", "compute"),
           ("Lexa AI", "ai_api"), ("Promptworks", "ai_api"), ("Deskline Supplies", "office_supplies"),
           ("Brightline Print Co.", "print"), ("Pageturn Books", "books"), ("CityCab", "rides"), ("Harborview Inn", "lodging"),
           ("Northwind Air", "flights"), ("Tallyhouse Software", "software"), ("Ledgerly", "software"),
           ("Mapwise", "data"), ("Vectorly", "ai_api"), ("Quillbase", "software"), ("Fernway Foods", "food")]
UNTRUSTED = [("QuickData Hub", "data"), ("Nimbus Resell", "compute"), ("Apex Vouchers", "gift_cards"),
             ("CoinRelay", "crypto_exchange"), ("Swiftpay Transfer", "money_transfer"), ("Orbit Tools", "software"),
             ("Pixel Forge Studio", "software"), ("Halcyon Consulting", "other"), ("Meridian Services", "other"),
             ("Kestrel Analytics", "data")]
LOOKALIKES = [("DataLoorn", "data"), ("C0reCloud", "compute"), ("Lexa-AI Billing", "ai_api")]


@dataclass
class Shift:
    seed: int
    registry: Registry
    txns: list[LedgerTxn]
    txn_pattern: dict[str, str]  # laundering txn id -> pattern name
    alerts: list[Alert]  # the queue (real rule output, sampled to the queue size)
    all_alerts: int = 0
    by_id: dict[str, LedgerTxn] = field(default_factory=dict)

    def alert_truth(self, a: Alert) -> dict:
        bad = [t for t in a.txn_ids if t in self.txn_pattern]
        return {"laundering": bool(bad), "laundering_micros": sum(self.by_id[t].amount for t in bad),
                "patterns": sorted({self.txn_pattern[t] for t in bad})}

    def laundering_total(self) -> int:
        return sum(self.by_id[t].amount for t in self.txn_pattern)


def _registry(rng: random.Random) -> Registry:
    reg = Registry()
    for i, (n, c) in enumerate(TRUSTED):
        reg.add_merchant(Merchant(f"m_t{i:02d}", n, c, trusted=True))
    for i, (n, c) in enumerate(UNTRUSTED + LOOKALIKES):
        reg.add_merchant(Merchant(f"m_u{i:02d}", n, c, trusted=False))
    teams = ["growth", "research", "finance", "ops", "platform"]
    for i in range(40):
        thr = rng.choice([usd(50), usd(100), usd(250), usd(500)])
        reg.add_agent(Agent(agent_id=f"agent_{i:02d}", name=f"agent_{i:02d}", role="purchasing", owner_id=teams[i % 5],
                            per_txn_limit=thr * 2, daily_budget=thr * 20, approval_threshold=thr,
                            allowed_merchants=frozenset(m for m in reg.merchants)))
    return reg


def generate(seed: int, queue_size: int = 60) -> Shift:
    rng = random.Random(seed)
    reg = _registry(rng)
    seq = itertools.count(1)
    txns: list[LedgerTxn] = []
    label: dict[str, str] = {}
    trusted = [m for m in reg.merchants.values() if m.trusted]
    untrusted = [m for m in reg.merchants.values() if not m.trusted and m.name not in dict(LOOKALIKES)]
    looks = [m for m in reg.merchants.values() if m.name in dict(LOOKALIKES)]
    agents = list(reg.agents.values())

    def pay(agent: Agent, merchant: Merchant, amount: int, at: datetime, pattern: str | None = None) -> None:
        amount = max(amount, 10_000)  # at least one cent
        t = LedgerTxn(txn_id=f"T{next(seq):07d}", kind=TxnKind.PAYMENT, timestamp=at, amount=amount,
                      postings=(Posting(agent.wallet_account, -amount), Posting(f"merchant:{merchant.merchant_id}", amount)),
                      agent_id=agent.agent_id, owner_id=agent.owner_id, merchant_id=merchant.merchant_id)
        txns.append(t)
        if pattern:
            label[t.txn_id] = pattern

    def when(day: float, hour_lo=8, hour_hi=19) -> datetime:
        return START + timedelta(days=int(day), hours=rng.uniform(hour_lo, hour_hi))

    dormant = rng.sample(agents, 2)
    # Normal activity.
    for a in agents:
        favs = rng.sample(trusted, rng.randint(2, 4))
        rate = rng.uniform(0.6, 4.0)
        for d in range(DAYS):
            if a in dormant and d < DAYS - 2:
                continue
            for _ in range(rng.choices(range(8), weights=[max(0.01, rate - abs(k - rate)) for k in range(8)])[0]):
                pay(a, rng.choice(favs), int(a.approval_threshold * min(0.75, rng.lognormvariate(-2.2, 0.7))), when(d))
    # Benign look-suspicious activity.
    for a in rng.sample(agents, 10):  # busy batch jobs: many small calls in a minute
        at = when(rng.randint(DAYS - PLANT_DAYS, DAYS - 1))
        for k in range(rng.randint(15, 22)):
            pay(a, rng.choice(trusted), int(a.approval_threshold * 0.02), at + timedelta(seconds=2 * k))
    for a in rng.sample(agents, 9):  # round-priced SaaS seats
        m = rng.choice([x for x in trusted if x.category == "software"])
        d = rng.randint(DAYS - PLANT_DAYS, DAYS - 1)
        for k in range(3):
            pay(a, m, usd(rng.choice([20, 30, 40])), when(d) + timedelta(minutes=10 * k))
    popular_tools = rng.sample([m for m in untrusted if m.category in ("software", "data", "other")], 3)
    popular = popular_tools[0]
    for tool in popular_tools:  # new tools many teams adopt the same day
        d = rng.randint(DAYS - PLANT_DAYS, DAYS - 1)
        for a in rng.sample(agents, rng.randint(3, 6)):
            pay(a, tool, usd(rng.choice([9, 12, 15])), when(d))
    for a in rng.sample(agents, 7):  # onboarding new vendors
        d = rng.randint(DAYS - PLANT_DAYS, DAYS - 1)
        for m in rng.sample(untrusted, 3):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.05, 0.3)), when(d))
    # Planted laundering (last 7 days).
    pool = [a for a in agents if a not in dormant]
    rng.shuffle(pool)
    it = iter(pool)
    plant_day = lambda: rng.randint(DAYS - PLANT_DAYS, DAYS - 1)
    for _ in range(3):  # structuring just under the approval threshold
        a, m, d = next(it), rng.choice(untrusted), plant_day()
        for k in range(rng.randint(3, 5)):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.86, 0.99)), when(d) + timedelta(hours=k), "structuring")
    team = [a for a in agents if a.owner_id == "ops"][:3]
    m, d = rng.choice(untrusted), plant_day()
    for a in team:  # team structuring
        for k in range(2):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.82, 0.97)), when(d) + timedelta(hours=k), "team structuring")
    for _ in range(2):  # rapid-fire drain
        a, m = next(it), rng.choice(untrusted)
        at = when(plant_day(), 0, 6)
        for k in range(rng.randint(16, 24)):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.1, 0.3)), at + timedelta(seconds=3 * k), "rapid-fire drain")
    for _ in range(2):  # fan-in: compromised agents paying one shell vendor
        m, d = rng.choice([x for x in untrusted if x not in popular_tools]), plant_day()
        for a in [next(it) for _ in range(rng.randint(3, 5))]:
            pay(a, m, int(a.approval_threshold * rng.uniform(0.4, 0.7)), when(d), "fan-in")
    for lk in looks:  # paying look-alike merchants
        a, d = next(it), plant_day()
        for k in range(rng.randint(1, 3)):
            pay(a, lk, int(a.approval_threshold * rng.uniform(0.3, 0.7)), when(d) + timedelta(hours=k), "look-alike merchant")
    for a in dormant:  # dormant then active
        m = rng.choice(untrusted)
        for k in range(rng.randint(3, 5)):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.3, 0.8)), when(DAYS - 1) + timedelta(minutes=20 * k), "dormant then active")
    for _ in range(2):  # round-amount transfers
        a, m, d = next(it), rng.choice(untrusted), plant_day()
        for k in range(3):
            pay(a, m, usd(rng.choice([100, 200, 500])), when(d) + timedelta(hours=k), "round amounts")
    hr = [m for m in untrusted if m.category in ("gift_cards", "crypto_exchange", "money_transfer")]
    for _ in range(3):  # cash-out through high-risk categories
        a, m, d = next(it), rng.choice(hr), plant_day()
        for k in range(rng.randint(1, 3)):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.5, 0.9)), when(d) + timedelta(hours=2 * k), "cash-out")
    for _ in range(2):  # slow drip under the band: designed to evade the rules
        a, m = next(it), rng.choice(untrusted)
        for d in range(DAYS - PLANT_DAYS, DAYS):
            pay(a, m, int(a.approval_threshold * rng.uniform(0.3, 0.5)), when(d), "slow drip (evades rules)")
    txns.sort(key=lambda t: (t.timestamp, t.txn_id))
    alerts = AmlMonitor(reg).scan(txns)
    cutoff = START + timedelta(days=DAYS - PLANT_DAYS)
    recent = [a for a in alerts if a.raised_at >= cutoff]
    queue = rng.sample(recent, min(queue_size, len(recent)))
    queue.sort(key=lambda a: a.raised_at)
    return Shift(seed, reg, txns, label, queue, len(recent), {t.txn_id: t for t in txns})


def score(shift: Shift, escalated: list[str], penalty: int = usd(50)) -> dict:
    """Laundering caught (distinct labelled transactions in escalated alerts), false alarms, and money
    recovered: labelled payments by the same subject AFTER the alert fired, which escalation would have
    stopped by holding the agent. ASSUMPTION: a false alarm costs $50 of analyst time (simulated)."""
    by_alert = {a.alert_id: a for a in shift.alerts}
    caught: set[str] = set()
    false_alarms = 0
    recovered: set[str] = set()
    for aid in escalated:
        a = by_alert[aid]
        bad = {t for t in a.txn_ids if t in shift.txn_pattern}
        if not bad:
            false_alarms += 1
            continue
        caught |= bad
        agents = {shift.by_id[t].agent_id for t in bad}
        recovered |= {t for t, _ in shift.txn_pattern.items()
                      if shift.by_id[t].agent_id in agents and shift.by_id[t].timestamp > a.raised_at}
    in_queue = {t for a in shift.alerts for t in a.txn_ids if t in shift.txn_pattern}
    amt = lambda s: sum(shift.by_id[t].amount for t in s)
    return {"caught_micros": amt(caught), "false_alarms": false_alarms, "recovered_micros": amt(recovered),
            "missed_in_queue_micros": amt(in_queue - caught), "never_alerted_micros": amt(set(shift.txn_pattern) - in_queue),
            "score_micros": amt(caught) - false_alarms * penalty}


def ranked(shift: Shift) -> list[str]:
    """AgentGuard's own queue order: severity, then total amount."""
    return [a.alert_id for a in sorted(shift.alerts, key=lambda a: (-a.severity, -sum(shift.by_id[t].amount for t in a.txn_ids)))]


def best(shift: Shift, budget: int) -> list[str]:
    """Best possible picks with the budget (greedy by laundering dollars)."""
    gain = lambda a: sum(shift.by_id[t].amount for t in a.txn_ids if t in shift.txn_pattern)
    return [a.alert_id for a in sorted(shift.alerts, key=lambda a: -gain(a))[:budget] if gain(a) > 0]
