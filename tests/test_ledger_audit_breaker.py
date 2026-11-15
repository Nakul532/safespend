"""Double-entry ledger, hash-chained audit log, circuit breaker."""
from __future__ import annotations

from dataclasses import replace

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from safespend import Merchant, ReasonCode as R, usd
from safespend.audit import AuditLog, EventType, verify_records
from safespend.circuit_breaker import BreakerError
from safespend.clock import ManualClock
from safespend.config import BreakerConfig, PolicyConfig
from safespend.fixtures import PRICES
from safespend.ledger import EXTERNAL_FUNDING, LedgerError
from conftest import OWNER_GROWTH, OWNER_MARKETS, START, make_guard, req

# == ledger ====================================================================


def test_payment_is_two_balanced_postings(guard):
    d = guard.submit_payment(req(amount=usd("0.002")))
    t = guard.ledger.get(d.txn_id)
    assert len(t.postings) == 2 and sum(p.amount for p in t.postings) == 0
    assert guard.ledger.balance("merchant:m_newshub") == usd("0.002")
    assert guard.ledger.balance("wallet:agent_001") == usd(100) - usd("0.002")
    assert guard.ledger.trial_balance() == 0


def test_ledger_refuses_to_overdraw_even_with_valid_permits(clock):
    """Two payments both validated while the wallet held enough for one: the second cannot settle."""
    g = make_guard(clock, fund=usd("0.003"))
    agent = g.registry.agents["agent_001"]
    r1, r2 = req(amount=usd("0.002")), req(merchant="m_finstream", amount=usd("0.002"))
    d1, d2 = g.validate_payment(r1), g.validate_payment(r2)
    assert d1.approved and d2.approved
    g.ledger.settle(d1.permit, r1, agent)
    with pytest.raises(LedgerError, match="negative"):
        g.ledger.settle(d2.permit, r2, agent)
    assert g.ledger.balance(agent.wallet_account) == usd("0.001")
    assert g.ledger.trial_balance() == 0


def test_funding_must_be_positive(guard):
    with pytest.raises(LedgerError):
        guard.ledger.fund(guard.registry.agents["agent_001"], 0)


def test_only_external_accounts_may_be_negative(guard):
    assert guard.ledger.balance(EXTERNAL_FUNDING) < 0
    assert all(v >= 0 for k, v in guard.ledger.balances().items() if not k.startswith("external:"))


_ops = st.lists(
    st.tuples(
        st.sampled_from(["agent_001", "agent_002", "agent_003"]),
        st.sampled_from(sorted(PRICES)),
        st.one_of(st.integers(min_value=1, max_value=usd("0.05")), st.integers(min_value=1, max_value=usd(12))),  # small + large (crosses limits)
        st.integers(min_value=0, max_value=4000),  # seconds to advance
        st.booleans(),  # reuse the previous idempotency key?
        st.sampled_from([None, "INV-A", "INV-B"]),
    ),
    max_size=60,
)


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(ops=_ops, fund=st.integers(min_value=0, max_value=usd(40)))
def test_property_ledger_always_reconciles(ops, fund):
    clock = ManualClock(START)
    g = make_guard(clock, fund=fund, policy=PolicyConfig(owner_daily_budgets={OWNER_GROWTH: usd(60)}))
    funded = {a: fund for a in g.registry.agents}
    last_key = None
    for i, (agent, merchant, amount, wait, reuse, inv) in enumerate(ops):
        clock.advance(seconds=wait)
        k = last_key if (reuse and last_key) else f"k{i}"
        last_key = k
        g.submit_payment(req(agent=agent, merchant=merchant, amount=amount, idempotency_key=k, invoice_ref=inv))

    # 1. Every entry balances and the whole ledger sums to zero.
    assert all(sum(p.amount for p in t.postings) == 0 for t in g.ledger.transactions())
    assert g.ledger.trial_balance() == 0
    # 2. Cached balances equal balances rebuilt from postings.
    rebuilt = g.ledger.recompute_balances()
    assert {k: v for k, v in rebuilt.items() if v} == {k: v for k, v in g.ledger.balances().items() if v}
    # 3. No wallet or merchant account is negative.
    assert all(v >= 0 for k, v in g.ledger.balances().items() if not k.startswith("external:"))
    # 4. Each wallet = funded - spent; merchants received exactly what wallets paid.
    for a in g.registry.agents:
        spent = sum(t.amount for t in g.ledger.payments() if t.agent_id == a)
        assert g.ledger.balance(f"wallet:{a}") == funded[a] - spent
    assert sum(v for k, v in g.ledger.balances().items() if k.startswith("merchant:")) == sum(
        t.amount for t in g.ledger.payments())
    # 5. Limits held: per-agent daily budget, per-txn limit, owner budget.
    for t in g.ledger.payments():
        agent = g.registry.agents[t.agent_id]
        assert t.amount <= agent.per_txn_limit
        assert t.merchant_id in agent.allowed_merchants
    by_day: dict = {}
    for t in g.ledger.payments():
        by_day.setdefault((t.agent_id, t.timestamp.date()), 0)
        by_day[(t.agent_id, t.timestamp.date())] += t.amount
    for (a, _), total in by_day.items():
        assert total <= g.registry.agents[a].daily_budget
    # 6. One idempotency key never settles twice; every settlement traces to an APPROVED decision.
    keys = [(t.agent_id, t.idempotency_key) for t in g.ledger.payments()]
    assert len(keys) == len(set(keys))
    approved = {r.payload["decision_id"] for r in g.audit.by_type(EventType.DECISION) if r.payload["outcome"] == "APPROVED"}
    assert all(t.decision_id in approved for t in g.ledger.payments())
    # 7. Payments at or above the approval threshold never settle without approval (none granted here).
    assert all(t.amount < g.registry.agents[t.agent_id].approval_threshold for t in g.ledger.payments())
    # 8. The audit chain verifies.
    assert g.verify_audit_log().ok


# == audit log =================================================================


def _busy_guard(clock):
    g = make_guard(clock)
    g.submit_payment(req())
    g.submit_payment(req(merchant="m_pixelmint"))
    g.submit_payment(req(amount=usd(3)))
    return g


def test_audit_chain_verifies(clock):
    g = _busy_guard(clock)
    res = g.verify_audit_log()
    assert res.ok and res.records_checked == len(g.audit.records()) >= 4


def test_edited_record_detected(clock):
    g = _busy_guard(clock)
    recs = g.audit.records()
    recs[1] = replace(recs[1], payload={**recs[1].payload, "outcome": "APPROVED"})
    res = verify_records(recs)
    assert not res.ok and res.first_bad_seq == 2


def test_edited_record_with_recomputed_hash_breaks_next_link(clock):
    from safespend.models import sha256_hex
    g = _busy_guard(clock)
    recs = g.audit.records()
    edited = replace(recs[1], payload={**recs[1].payload, "outcome": "APPROVED"})
    recs[1] = replace(edited, hash=sha256_hex(edited.body()))
    res = verify_records(recs)
    assert not res.ok and res.first_bad_seq == 3


def test_deleted_record_detected(clock):
    g = _busy_guard(clock)
    recs = g.audit.records()
    del recs[1]
    assert not verify_records(recs).ok


def test_export_round_trip_verifies_and_detects_edit(clock):
    g = _busy_guard(clock)
    text = g.audit.export_jsonl()
    assert verify_records(AuditLog.load_jsonl(text)).ok
    tampered = text.replace('"BLOCKED"', '"APPROVED"', 1)
    assert tampered != text and not verify_records(AuditLog.load_jsonl(tampered)).ok


# == circuit breaker =============================================================


def test_spend_spike_trips_breaker_and_blocks_everyone(clock):
    g = make_guard(clock, breaker=BreakerConfig(spend_window_seconds=600, spend_limit=usd("1.50")))
    g.submit_payment(req(amount=usd("1.00")))
    clock.advance(seconds=10)
    g.submit_payment(req(amount=usd("0.60")))  # pushes window spend to $1.60
    assert g.breaker.is_open
    other_team = g.submit_payment(req(agent="agent_002", merchant="m_finstream", amount=usd("0.005")))
    assert other_team.reason_code is R.CIRCUIT_BREAKER_OPEN
    trip = g.audit.by_type(EventType.BREAKER_TRIPPED)[-1]
    assert trip.payload["agents"] == ["agent_001"] and trip.payload["owners"] == [OWNER_GROWTH]


def test_spend_under_limit_does_not_trip(clock):
    g = make_guard(clock, breaker=BreakerConfig(spend_window_seconds=600, spend_limit=usd("1.50")))
    g.submit_payment(req(amount=usd("1.00")))
    clock.advance(seconds=601)
    g.submit_payment(req(amount=usd("0.60")))  # the first payment left the window
    assert not g.breaker.is_open


def test_alert_volume_trips_breaker(clock):
    g = make_guard(clock, breaker=BreakerConfig(alert_limit=1, spend_limit=usd(10_000)))
    g.registry.add_merchant(Merchant("m_gift", "GiftBox Cards", "gift_cards"))
    g.registry.agents["agent_002"] = replace(g.registry.agents["agent_002"],
                                             allowed_merchants=frozenset({"m_gift", "m_finstream"}))
    g.submit_payment(req(agent="agent_002", merchant="m_gift", amount=usd(1)))
    assert g.run_monitoring() and g.breaker.is_open


def test_owner_of_involved_agent_cannot_resume(clock):
    g = make_guard(clock, breaker=BreakerConfig(spend_limit=usd("0.50")))
    g.submit_payment(req(amount=usd(1)))
    with pytest.raises(BreakerError, match="four-eyes"):
        g.resume_spending(OWNER_GROWTH)
    for who in ("agent_001", "user_random"):
        with pytest.raises(BreakerError):
            g.resume_spending(who)
    assert g.breaker.is_open
    assert len(g.audit.by_type(EventType.BREAKER_RESUME_REFUSED)) == 3


def test_independent_approver_resumes_and_it_is_logged(clock):
    g = make_guard(clock, breaker=BreakerConfig(spend_limit=usd("0.50")))
    g.submit_payment(req(amount=usd(1)))
    g.resume_spending(OWNER_MARKETS)  # owns no involved agent
    assert not g.breaker.is_open
    rec = g.audit.by_type(EventType.BREAKER_RESUMED)[-1]
    assert rec.payload["approver_id"] == OWNER_MARKETS and rec.policy_version == g.policy_config.version
    # Spending before the resume does not immediately re-trip it.
    assert g.submit_payment(req(amount=usd("0.10"))).approved and not g.breaker.is_open
