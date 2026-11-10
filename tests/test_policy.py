"""Every policy check has a test where it fires and one where it does not."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from agentguard import Merchant, Outcome, ReasonCode as R, usd
from agentguard.audit import EventType
from agentguard.config import PolicyConfig
from agentguard.models import AgentStatus
from agentguard.policy import PolicyEngine
from agentguard.sanctions import ExactListScreener
from conftest import OWNER_GROWTH, codes, make_guard, req


def set_agent(guard, agent_id, **changes):
    guard.registry.agents[agent_id] = replace(guard.registry.agents[agent_id], **changes)


def test_happy_path_settles(guard):
    d = guard.submit_payment(req())
    assert d.outcome is Outcome.APPROVED and d.reason_code is R.APPROVED
    assert d.failed_checks == () and d.txn_id is not None
    assert d.checks_evaluated == tuple(name for name, _ in PolicyEngine.CHECK_ORDER)


# -- circuit breaker -----------------------------------------------------------

def test_breaker_open_blocks(guard):
    guard.breaker.trip("manual test", ["agent_001"])
    d = guard.submit_payment(req())
    assert d.reason_code is R.CIRCUIT_BREAKER_OPEN and d.outcome is Outcome.BLOCKED


def test_breaker_closed_does_not_block(guard):
    assert R.CIRCUIT_BREAKER_OPEN not in codes(guard.submit_payment(req()))


# -- agent ---------------------------------------------------------------------

def test_unknown_agent_blocked(guard):
    assert guard.submit_payment(req(agent="agent_999")).reason_code is R.AGENT_UNKNOWN


def test_known_agent_passes(guard):
    assert R.AGENT_UNKNOWN not in codes(guard.submit_payment(req(agent="agent_001")))


def test_suspended_agent_blocked(guard):
    set_agent(guard, "agent_001", status=AgentStatus.SUSPENDED)
    assert guard.submit_payment(req()).reason_code is R.AGENT_SUSPENDED


def test_active_agent_passes(guard):
    assert R.AGENT_SUSPENDED not in codes(guard.submit_payment(req()))


# -- amount ----------------------------------------------------------------------

@pytest.mark.parametrize("amount,currency", [(0, "USD"), (-5, "USD"), (usd("0.002"), "EUR")])
def test_invalid_amount_blocked(guard, amount, currency):
    assert guard.submit_payment(req(amount=amount, currency=currency)).reason_code is R.INVALID_AMOUNT


def test_valid_amount_passes(guard):
    assert R.INVALID_AMOUNT not in codes(guard.submit_payment(req(amount=1)))


# -- merchant --------------------------------------------------------------------

def test_unknown_merchant_blocked(guard):
    assert guard.submit_payment(req(merchant="m_nowhere")).reason_code is R.MERCHANT_UNKNOWN


def test_known_merchant_passes(guard):
    assert R.MERCHANT_UNKNOWN not in codes(guard.submit_payment(req()))


@pytest.mark.parametrize("fake_name", ["N3wsHub", "NewsHúb", "Nеwshub", "NewsHub Inc", "NewsHubb"])  # 'е' is Cyrillic
def test_lookalike_merchant_blocked_and_listed_with_allowlist_failure(guard, fake_name):
    guard.registry.add_merchant(Merchant("m_fake", fake_name, "data", trusted=False))
    d = guard.submit_payment(req(merchant="m_fake"))
    assert d.reason_code is R.LOOKALIKE_MERCHANT
    assert codes(d)[:2] == [R.LOOKALIKE_MERCHANT, R.MERCHANT_NOT_ALLOWLISTED]


def test_unrelated_untrusted_merchant_is_not_lookalike(guard):
    guard.registry.add_merchant(Merchant("m_zen", "Zentrix Analytics", "data", trusted=False))
    d = guard.submit_payment(req(merchant="m_zen"))
    assert d.reason_code is R.MERCHANT_NOT_ALLOWLISTED and R.LOOKALIKE_MERCHANT not in codes(d)


def test_not_allowlisted_blocked(guard):
    assert guard.submit_payment(req(merchant="m_pixelmint")).reason_code is R.MERCHANT_NOT_ALLOWLISTED


def test_allowlisted_passes(guard):
    assert R.MERCHANT_NOT_ALLOWLISTED not in codes(guard.submit_payment(req(merchant="m_finstream", amount=usd("0.005"))))


# -- sanctions (Stage 1 interface; fictional list) ------------------------------------

def _sanctions_guard(clock):
    screener = ExactListScreener(["Kestrel Volga Trading"], list_name="TEST LIST (fictional)", list_date="2026-11-01")
    g = make_guard(clock, sanctions=screener)
    g.registry.add_merchant(Merchant("m_kvt", "KESTREL-VOLGA trading", "data"))
    g.registry.add_merchant(Merchant("m_clean", "Bluefin Data", "data"))
    set_agent(g, "agent_001", allowed_merchants=frozenset({"m_kvt", "m_clean"}))
    return g


def test_sanctions_hit_blocked(clock):
    d = _sanctions_guard(clock).submit_payment(req(merchant="m_kvt"))
    assert d.reason_code is R.SANCTIONS_HIT and "2026-11-01" in d.failed_checks[0].detail


def test_sanctions_clean_passes(clock):
    assert _sanctions_guard(clock).submit_payment(req(merchant="m_clean")).approved


# -- limits ----------------------------------------------------------------------

def test_per_txn_limit_blocked(guard):
    assert guard.submit_payment(req(amount=usd("5.01"))).reason_code is R.PER_TXN_LIMIT_EXCEEDED


def test_at_per_txn_limit_not_blocked_by_that_check(guard):
    assert R.PER_TXN_LIMIT_EXCEEDED not in codes(guard.submit_payment(req(amount=usd(5))))


def test_merchant_daily_limit(guard, clock):
    set_agent(guard, "agent_001", merchant_daily_limits={"m_newshub": usd("0.005")})
    assert guard.submit_payment(req(amount=usd("0.002"))).approved
    clock.advance(seconds=10)
    assert guard.submit_payment(req(amount=usd("0.003"))).approved  # exactly at the limit
    clock.advance(seconds=10)
    assert guard.submit_payment(req(amount=usd("0.001"))).reason_code is R.MERCHANT_LIMIT_EXCEEDED
    # Other merchants are unaffected.
    assert guard.submit_payment(req(merchant="m_finstream", amount=usd("0.001"))).approved


def test_daily_budget_blocks_then_resets_at_utc_midnight(guard, clock):
    set_agent(guard, "agent_001", daily_budget=usd("0.010"))
    assert guard.submit_payment(req(amount=usd("0.010"))).approved
    clock.advance(seconds=10)
    assert guard.submit_payment(req(amount=usd("0.001"))).reason_code is R.BUDGET_EXCEEDED
    clock.set(clock.now().replace(hour=0, minute=0, second=0) + timedelta(days=1))
    assert guard.submit_payment(req(amount=usd("0.001"))).approved


def test_within_budget_passes(guard):
    assert R.BUDGET_EXCEEDED not in codes(guard.submit_payment(req(amount=usd("1.00"))))


# -- owner-level (team) aggregation ---------------------------------------------------

def test_owner_daily_budget_spans_agents(clock):
    g = make_guard(clock, policy=PolicyConfig(owner_daily_budgets={OWNER_GROWTH: usd("0.010")}))
    assert g.submit_payment(req(agent="agent_001", amount=usd("0.006"))).approved
    d = g.submit_payment(req(agent="agent_003", amount=usd("0.005")))  # agent_003's own budget is fine
    assert d.reason_code is R.OWNER_BUDGET_EXCEEDED
    # A different owner's agent is not affected.
    assert g.submit_payment(req(agent="agent_002", merchant="m_finstream", amount=usd("0.005"))).approved


def test_owner_budget_not_reached_passes(clock):
    g = make_guard(clock, policy=PolicyConfig(owner_daily_budgets={OWNER_GROWTH: usd(1)}))
    g.submit_payment(req(agent="agent_001", amount=usd("0.006")))
    assert g.submit_payment(req(agent="agent_003", amount=usd("0.005"))).approved


def test_owner_velocity_spans_agents(clock):
    g = make_guard(clock, policy=PolicyConfig(owner_max_payments_per_window=3))
    for agent, amt in (("agent_001", "0.001"), ("agent_001", "0.002"), ("agent_003", "0.003")):
        assert g.submit_payment(req(agent=agent, amount=usd(amt))).approved
        clock.advance(seconds=1)
    assert g.submit_payment(req(agent="agent_003", amount=usd("0.004"))).reason_code is R.OWNER_VELOCITY_EXCEEDED
    assert g.submit_payment(req(agent="agent_002", merchant="m_finstream", amount=usd("0.005"))).approved
    clock.advance(seconds=61)
    assert g.submit_payment(req(agent="agent_003", amount=usd("0.004"))).approved


# -- velocity -------------------------------------------------------------------------

def test_agent_velocity(guard, clock):
    set_agent(guard, "agent_001", max_payments_per_window=3)
    for amt in ("0.001", "0.002", "0.003"):
        assert guard.submit_payment(req(amount=usd(amt))).approved
        clock.advance(seconds=1)
    assert guard.submit_payment(req(amount=usd("0.004"))).reason_code is R.VELOCITY_EXCEEDED


def test_velocity_window_expires(guard, clock):
    set_agent(guard, "agent_001", max_payments_per_window=3)
    for amt in ("0.001", "0.002", "0.003"):
        guard.submit_payment(req(amount=usd(amt)))
    clock.advance(seconds=61)
    assert guard.submit_payment(req(amount=usd("0.004"))).approved


# -- duplicate heuristic (backup to idempotency keys) ------------------------------------

def test_same_invoice_new_key_is_duplicate(guard, clock):
    assert guard.submit_payment(req(amount=usd("0.002"), invoice_ref="INV-1")).approved
    clock.advance(hours=3)
    assert guard.submit_payment(req(amount=usd("0.002"), invoice_ref="INV-1")).reason_code is R.DUPLICATE_SUSPECTED


def test_different_invoice_is_not_duplicate(guard):
    guard.submit_payment(req(amount=usd("0.002"), invoice_ref="INV-1"))
    assert guard.submit_payment(req(amount=usd("0.002"), invoice_ref="INV-2")).approved


def test_same_payment_seconds_apart_is_duplicate_but_later_is_not(guard, clock):
    assert guard.submit_payment(req()).approved
    clock.advance(seconds=2)
    assert guard.submit_payment(req()).reason_code is R.DUPLICATE_SUSPECTED
    clock.advance(seconds=10)
    assert guard.submit_payment(req()).approved  # an agent calling the same API again later is normal


# -- funds ----------------------------------------------------------------------------

def test_insufficient_funds(clock):
    g = make_guard(clock, fund=usd("0.001"))
    assert g.submit_payment(req(amount=usd("0.002"))).reason_code is R.INSUFFICIENT_FUNDS


def test_sufficient_funds(clock):
    g = make_guard(clock, fund=usd("0.002"))
    assert g.submit_payment(req(amount=usd("0.002"))).approved


# -- approval threshold ------------------------------------------------------------------

def test_at_threshold_needs_approval(guard):
    d = guard.submit_payment(req(amount=usd(2)))
    assert d.outcome is Outcome.PENDING_APPROVAL and d.reason_code is R.APPROVAL_REQUIRED and d.txn_id is None


def test_below_threshold_needs_no_approval(guard):
    assert guard.submit_payment(req(amount=usd("1.99"))).approved


# -- first failure decides, every failure is recorded ----------------------------------------

def test_first_failure_decides_but_audit_lists_all(guard):
    d = guard.submit_payment(req(merchant="m_pixelmint", amount=usd(6)))
    assert d.outcome is Outcome.BLOCKED
    assert d.reason_code is R.MERCHANT_NOT_ALLOWLISTED
    assert codes(d) == [R.MERCHANT_NOT_ALLOWLISTED, R.PER_TXN_LIMIT_EXCEEDED, R.APPROVAL_REQUIRED]
    rec = guard.audit.by_type(EventType.DECISION)[-1]
    assert rec.payload["reason_code"] == "MERCHANT_NOT_ALLOWLISTED"
    assert [f["code"] for f in rec.payload["failed_checks"]] == [
        "MERCHANT_NOT_ALLOWLISTED", "PER_TXN_LIMIT_EXCEEDED", "APPROVAL_REQUIRED"]
    assert len(rec.payload["checks_evaluated"]) == len(PolicyEngine.CHECK_ORDER)


def test_blocked_payment_is_not_pending_even_if_it_also_needs_approval(guard):
    d = guard.submit_payment(req(merchant="m_pixelmint", amount=usd(3)))
    assert d.outcome is Outcome.BLOCKED


# -- policy version -----------------------------------------------------------------------

def test_policy_version_and_hash_recorded(clock):
    g = make_guard(clock, policy=PolicyConfig(version="policy-test-7"))
    d = g.submit_payment(req())
    rec = g.audit.by_type(EventType.DECISION)[-1]
    assert d.policy_version == "policy-test-7" == rec.policy_version
    assert rec.payload["policy_hash"] == d.policy_hash == g.policy_config.config_hash


def test_policy_hash_changes_with_any_setting():
    assert PolicyConfig().config_hash != PolicyConfig(velocity_window_seconds=61).config_hash
    assert PolicyConfig().config_hash == PolicyConfig().config_hash
