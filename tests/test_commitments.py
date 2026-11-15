"""Recurring-commitment and stored-credential holds. ADDED AFTER LOCK (Stage 4 game, level 4)."""
from __future__ import annotations

from safespend import Commitment, Outcome, ReasonCode as R, usd
from safespend.commitments import detect_terms, worst_case
from safespend.config import PolicyConfig
from conftest import RISK_OFFICER, make_guard, replace, req

TRIAL = {"task": "Sign up for the code-search tool", "merchant_page": "Start your free trial: $0 today, then $49/month."}
TOPUP = {"task": "Buy API credits", "merchant_page": "Credits $5. Auto top-up when your balance runs low (recommended)."}
CARD = {"task": "Buy one report", "checkout": "[x] Save this card for faster checkout next time"}
PLAIN = {"task": "Buy one article", "merchant_page": "Article: $0.50, one-time purchase."}


def g(clock, on=True):
    return make_guard(clock, policy=PolicyConfig(commitment_check=on))


def test_zero_dollar_trial_that_converts_is_held_not_invalid(clock):
    d = g(clock).submit_payment(req(merchant="m_newshub", amount=0, context=TRIAL))
    assert d.outcome is Outcome.PENDING_APPROVAL and d.reason_code is R.RECURRING_COMMITMENT
    assert "did not declare" in d.failed_checks[0].detail


def test_declared_commitment_shows_worst_case(clock):
    c = Commitment("recurring", usd(49), 30)
    d = g(clock).submit_payment(req(amount=0, commitment=c))
    assert d.reason_code is R.RECURRING_COMMITMENT and "$637" in d.failed_checks[0].detail  # 13 periods in 365 days
    assert worst_case(c, 365) == usd(49) * 13


def test_auto_topup_has_no_upper_limit(clock):
    d = g(clock).submit_payment(req(amount=usd("0.50"), context=TOPUP))
    assert d.reason_code is R.RECURRING_COMMITMENT
    assert worst_case(Commitment("auto_topup", usd(5), None), 365) is None


def test_pre_ticked_saved_card_is_held(clock):
    d = g(clock).submit_payment(req(amount=usd("0.50"), context=CARD))
    assert d.outcome is Outcome.PENDING_APPROVAL and d.reason_code is R.STORED_CREDENTIAL
    d2 = g(clock).submit_payment(req(amount=usd("0.50"), store_credential=True))
    assert d2.reason_code is R.STORED_CREDENTIAL


def test_human_approval_releases_and_commitment_is_recorded(clock):
    guard = g(clock)
    r = req(amount=0, commitment=Commitment("trial_conversion", usd(49), 30), context=TRIAL)
    d = guard.submit_payment(r)
    ok = guard.submit_payment(replace(r, approval=guard.grant_approval(d.payment_hash, RISK_OFFICER)))
    assert ok.approved and ok.txn_id
    assert guard.future_commitments[0]["worst_case"] == usd(49) * 13


def test_approval_is_bound_to_the_terms(clock):
    a = req(amount=0, idempotency_key="k1", commitment=Commitment("recurring", usd(49), 30))
    b = replace(a, commitment=Commitment("recurring", usd(499), 30))
    assert a.payment_hash != b.payment_hash
    plain = req(idempotency_key="k2")
    assert "commitment" not in plain.financial_fields() and "store_credential" not in plain.financial_fields()


def test_one_time_purchase_passes_and_switch_off_is_stage1(clock):
    assert g(clock).submit_payment(req(amount=usd("0.50"), context=PLAIN)).approved
    off = g(clock, on=False)
    assert off.submit_payment(req(amount=0, context=TRIAL)).reason_code is R.INVALID_AMOUNT
    assert off.submit_payment(req(amount=usd("0.50"), context=TOPUP)).approved


def test_detection_patterns():
    assert detect_terms(TRIAL).kinds[:1] == ("trial_conversion",)
    assert detect_terms(CARD).credential
    assert detect_terms(PLAIN).kinds == () and not detect_terms(PLAIN).credential
    assert "recurring" in detect_terms({"p": "Billed annually. Renews automatically."}).kinds


def test_disabled_checks_skip_and_are_audited(clock):
    from safespend.audit import EventType
    guard = make_guard(clock, policy=PolicyConfig(disabled_checks=frozenset({"merchant_allowlist"})))
    d = guard.submit_payment(req(merchant="m_oracleai"))  # not on agent_001's allowlist
    assert d.approved and "merchant_allowlist" not in d.checks_evaluated
    rec = guard.audit.by_type(EventType.DECISION)[-1]
    assert rec.payload["checks_skipped"] == ["merchant_allowlist"]
    import pytest
    with pytest.raises(ValueError):
        make_guard(clock, policy=PolicyConfig(disabled_checks=frozenset({"nope"}))).submit_payment(req())
