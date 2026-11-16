"""Evidence pack for an AML alert (investigator v4). Computed by code; every line has an ID [E1], [E2], ...

The investigator model may only interpret these lines and cite their IDs. Every figure here comes from the ledger,
covers ALL of the alert's payments (not only the rows shown), and is shown to the analyst next to the model's words.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .aml.rules import Alert
from .money import fmt_usd

PACK_VERSION = "p3"  # p3 (post-results): code-computed timing labels on span and busiest-stretch lines
# p2: p2: cross-alert links via untrusted merchants only (trusted vendors everyone uses are noise); single-payment wording
MAX_ROWS, LARGEST, MAX_SWITCHES, MAX_LINKS = 25, 5, 5, 6
BURST_WINDOW = timedelta(minutes=10)


@dataclass(frozen=True)
class Fact:
    id: str
    kind: str  # rule | overview | agent | span | burst | merchant | switch | largest | link | history
    text: str
    txns: tuple[str, ...] = ()
    data: dict = field(default_factory=dict, hash=False, compare=False)


@dataclass
class Pack:
    alert: Alert
    facts: list[Fact]
    rows: list  # LedgerTxn shown to the model and the analyst, in time order
    total_payments: int
    pct: dict[str, float]  # txn id -> amount as % of its agent's approval threshold

    def by_id(self) -> dict[str, Fact]:
        return {f.id: f for f in self.facts}

    def text(self, registry) -> str:
        a = self.alert
        lines = [f"Alert {a.alert_id}: rule {a.rule}, severity {a.severity}, subject {a.subject_type} {a.subject_id}.", "",
                 "Evidence pack (computed by code from the ledger; cite these IDs):"]
        lines += [f"[{f.id}] {f.text}" for f in self.facts]
        shown = f"{len(self.rows)} of {self.total_payments} shown" if len(self.rows) < self.total_payments else "all shown"
        lines += ["", f"Transactions ({shown}; the pack above covers all of them):"]
        lines += [row_text(t, registry, self.pct) for t in self.rows]
        return "\n".join(lines)


def dur(td: timedelta) -> str:
    s = int(td.total_seconds())
    if s < 60:
        return f"{s} s"
    m = s // 60
    if m < 60:
        return f"{m} m"
    h, m = divmod(m, 60)
    if h < 48:
        return f"{h} h {m} m"
    d, h = divmod(h, 24)
    return f"{d} d {h} h"


def timing_label(seconds: float) -> str:
    """The only words the investigator may use about timing (pack p3). Computed by code."""
    h = seconds / 3600
    if seconds < 60:
        return "within a minute"
    if seconds < 600:
        return "within minutes"
    if h <= 1:
        return "within an hour"
    if h <= 24:
        return "within one day"
    if h <= 72:
        return f"over about {round(h)} hours"
    return f"over about {round(h / 24)} days"


def ts(t: datetime) -> str:
    return f"{t:%m-%d %H:%M}"


def row_text(t, registry, pct) -> str:
    a, m = registry.agents.get(t.agent_id), registry.merchants.get(t.merchant_id)
    return (f"{t.txn_id} | {t.timestamp:%Y-%m-%d %H:%M} | {t.agent_id} (team {a.owner_id if a else '?'}, approval threshold "
            f"{fmt_usd(a.approval_threshold) if a else '?'}) | {m.name if m else t.merchant_id} ({m.category if m else '?'}, "
            f"{'trusted' if m and m.trusted else 'untrusted'}) | {fmt_usd(t.amount)} ({pct.get(t.txn_id, 0):.1f}% of threshold)")


def _densest(txns: list) -> list:
    """Largest set of payments inside any BURST_WINDOW."""
    best, j = [], 0
    for i in range(len(txns)):
        while txns[i].timestamp - txns[j].timestamp > BURST_WINDOW:
            j += 1
        if i - j + 1 > len(best):
            best = txns[j:i + 1]
    return best


def build(alert: Alert, txns_by_id: dict, registry, *, pool=(), queue=frozenset(), history=None) -> Pack:
    txns = sorted((txns_by_id[t] for t in alert.txn_ids), key=lambda t: (t.timestamp, t.txn_id))
    thr = {t.txn_id: registry.agents[t.agent_id].approval_threshold for t in txns if t.agent_id in registry.agents}
    pct = {t.txn_id: 100.0 * t.amount / thr[t.txn_id] for t in txns if thr.get(t.txn_id)}
    mname = lambda mid: registry.merchants[mid].name if mid in registry.merchants else mid
    facts: list[Fact] = []
    ids = tuple(t.txn_id for t in txns)

    def add(kind, text, tx=(), **data):
        facts.append(Fact(f"E{len(facts) + 1}", kind, text, tuple(tx), data))

    add("rule", f"Rule explanation (computed by code, true): {alert.explanation}", ids)
    agents = sorted({t.agent_id for t in txns})
    merchants = sorted({t.merchant_id for t in txns}, key=mname)
    add("overview", f"{len(txns)} payment{'s' if len(txns) != 1 else ''} totalling {fmt_usd(sum(t.amount for t in txns))}, "
        f"from {len(agents)} agent{'s' if len(agents) != 1 else ''} to {len(merchants)} merchant{'s' if len(merchants) != 1 else ''}.",
        ids, payments=len(txns), agents=len(agents), merchants=len(merchants))
    # Per agent: count, total, amount as % of its approval threshold.
    by_agent = defaultdict(list)
    for t in txns:
        by_agent[t.agent_id].append(t)
    for ag, ts_ in sorted(by_agent.items()):
        a = registry.agents.get(ag)
        ps = [pct[t.txn_id] for t in ts_ if t.txn_id in pct]
        rng = f"at {min(ps):.1f}%" if len(ps) == 1 else f"each {min(ps):.1f}%–{max(ps):.1f}%"
        add("agent", f"{ag} (team {a.owner_id if a else '?'}): {len(ts_)} payment{'s' if len(ts_) != 1 else ''}, "
            f"{fmt_usd(sum(t.amount for t in ts_))}, {rng} of its {fmt_usd(a.approval_threshold) if a else '?'} approval threshold.",
            [t.txn_id for t in ts_], min_pct=min(ps) if ps else None, max_pct=max(ps) if ps else None)
    # Time span, and the busiest window.
    span = txns[-1].timestamp - txns[0].timestamp
    add("span", f"First payment {ts(txns[0].timestamp)}, last {ts(txns[-1].timestamp)}: all {len(txns)} within {dur(span)}. "
        f"Timing label: \"{timing_label(span.total_seconds())}\".", ids, span_s=span.total_seconds(), label=timing_label(span.total_seconds()))
    dense = _densest(txns)
    if len(dense) >= 3 and len(dense) < len(txns) or (len(dense) >= 3 and span <= BURST_WINDOW):
        ds = dense[-1].timestamp - dense[0].timestamp
        add("burst", f"Busiest stretch: {len(dense)} payments within {dur(ds)} ({ts(dense[0].timestamp)}–{dense[-1].timestamp:%H:%M}). "
            f"Timing label: \"{timing_label(ds.total_seconds())}\".", [t.txn_id for t in dense], span_s=ds.total_seconds(),
            payments=len(dense), label=timing_label(ds.total_seconds()))
    # Per merchant: trust, category, count, total, agents.
    for mid in merchants:
        m = registry.merchants.get(mid)
        mt = [t for t in txns if t.merchant_id == mid]
        n_ag = len({t.agent_id for t in mt})
        add("merchant", f"{mname(mid)} ({m.category if m else '?'}, {'trusted' if m and m.trusted else 'untrusted'}): "
            f"{len(mt)} payment{'s' if len(mt) != 1 else ''}, {fmt_usd(sum(t.amount for t in mt))}, from {n_ag} agent{'s' if n_ag != 1 else ''}.",
            [t.txn_id for t in mt], trusted=bool(m and m.trusted), category=m.category if m else None)
    # Merchant switches per agent.
    sw = 0
    for ag, ts_ in sorted(by_agent.items()):
        for p, q in zip(ts_, ts_[1:]):
            if p.merchant_id != q.merchant_id and sw < MAX_SWITCHES:
                sw += 1
                add("switch", f"{ag} switched from {mname(p.merchant_id)} to {mname(q.merchant_id)} between "
                    f"{ts(p.timestamp)} and {ts(q.timestamp)} ({dur(q.timestamp - p.timestamp)} apart).", [p.txn_id, q.txn_id])
    # Largest payments: always in the pack and in the shown rows.
    top = sorted(txns, key=lambda t: (-t.amount, t.txn_id))[:LARGEST]
    add("largest", "Largest payments: " + "; ".join(f"{t.txn_id} {fmt_usd(t.amount)} ({t.agent_id} to {mname(t.merchant_id)}, "
                                                    f"{ts(t.timestamp)})" for t in top) + ".", [t.txn_id for t in top])
    # Cross-alert links: other alerts sharing a merchant, owner or agent.
    mine_m = {m for m in merchants if m in registry.merchants and not registry.merchants[m].trusted}
    mine_a = set(agents)
    mine_o = {t.owner_id for t in txns}
    links = 0
    for o in sorted(pool, key=lambda x: (x.raised_at, x.alert_id)):
        if o.alert_id == alert.alert_id or links >= MAX_LINKS:
            continue
        ot = [txns_by_id[t] for t in o.txn_ids if t in txns_by_id]
        shared = []
        if mine_m & {t.merchant_id for t in ot}:
            shared.append("merchant " + ", ".join(sorted(mname(x) for x in mine_m & {t.merchant_id for t in ot})))
        if mine_a & {t.agent_id for t in ot}:
            shared.append("agent " + ", ".join(sorted(mine_a & {t.agent_id for t in ot})))
        elif alert.subject_type == "owner" and o.subject_type == "owner" and o.subject_id in mine_o:
            shared.append(f"owner {o.subject_id}")
        if shared:
            links += 1
            add("link", f"Also flagged: {o.alert_id} ({str(o.rule).replace('AML_', '').replace('_', ' ').lower()}, severity {o.severity}, "
                f"{'in your queue' if o.alert_id in queue else 'not in your queue'}, raised {ts(o.raised_at)}) shares {'; '.join(shared)}.",
                alert=o.alert_id)
    if history:
        usual = Counter(mname(t.merchant_id) for t in history)
        days = max(1.0, (history[-1].timestamp - history[0].timestamp).total_seconds() / 86400)
        add("history", f"Before this alert, {alert.subject_id} made {len(history)} payments over {dur(history[-1].timestamp - history[0].timestamp)} "
            f"(about {len(history) / days:.1f} a day), mostly to " + ", ".join(n for n, _ in usual.most_common(4)) + ".")
    # Rows: the largest always, then the rest in time order, up to MAX_ROWS.
    keep = {t.txn_id for t in top}
    for t in txns:
        if len(keep) >= MAX_ROWS:
            break
        keep.add(t.txn_id)
    rows = [t for t in txns if t.txn_id in keep]
    return Pack(alert, facts, rows, len(txns), pct)
