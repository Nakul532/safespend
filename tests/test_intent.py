"""Intent check (ADDED AFTER LOCK, Stage 4). The LLM is mocked."""
from __future__ import annotations

import json

from safespend import Outcome, ReasonCode as R, usd
from safespend.intent import Intent, IntentChecker, field_checks
from safespend.llm import MockLlmClient
from conftest import RISK_OFFICER, make_guard, replace, req
from safespend import SafeSpend
from safespend.fixtures import demo_registry
from safespend.config import BreakerConfig

OK = json.dumps({"mismatch": False, "confidence": "high", "reasons": ["same thing"]})
BAD = json.dumps({"mismatch": True, "confidence": "high", "reasons": ["an annual plan, not one month"]})
WANT = Intent("Buy one article from NewsHub.", max_amount=usd(1))


def guard(clock, reply=OK, llm=True):
    ck = IntentChecker(MockLlmClient(lambda m: reply) if llm else None)
    g = SafeSpend(demo_registry(), clock=clock, intent_checker=ck,
                   breaker=BreakerConfig(spend_limit=usd(10_000), alert_limit=1000))
    for a in g.registry.agents:
        g.fund(a, usd(100))
    return g


def test_model_flag_holds_and_human_releases(clock):
    g = guard(clock, BAD)
    r = req(amount=usd("0.50"), description="annual plan", intent=WANT)
    d = g.submit_payment(r)
    assert d.outcome is Outcome.PENDING_APPROVAL and d.reason_code is R.INTENT_MISMATCH
    assert g.submit_payment(replace(r, approval=g.grant_approval(d.payment_hash, RISK_OFFICER))).approved


def test_match_passes_and_no_intent_means_no_check(clock):
    g = guard(clock, OK)
    assert g.submit_payment(req(amount=usd("0.50"), description="one article", intent=WANT)).approved
    assert g.submit_payment(req(amount=usd("0.60"))).approved


def test_field_checks_decide_without_model(clock):
    g = guard(clock, OK, llm=False)
    d = g.submit_payment(req(amount=usd("2.00"), description="one article", intent=WANT))
    assert d.reason_code is R.INTENT_MISMATCH  # over the person's limit
    assert field_checks(Intent("buy a book"), usd(50), "gift_cards")
    assert not field_checks(Intent("buy a book", categories=frozenset({"books"})), usd(50), "books")


def test_low_confidence_does_not_hold_and_errors_fail_closed(clock):
    low = json.dumps({"mismatch": True, "confidence": "low", "reasons": ["unsure"]})
    assert guard(clock, low).submit_payment(req(amount=usd("0.50"), description="x", intent=WANT)).approved
    assert guard(clock, "not json").submit_payment(req(amount=usd("0.50"), description="x", intent=WANT)).reason_code is R.INTENT_MISMATCH


def test_reasons_with_digits_are_dropped():
    ck = IntentChecker(MockLlmClient(lambda m: json.dumps({"mismatch": True, "confidence": "high", "reasons": ["costs 12 more"]})))
    res = ck.check(WANT, amount=usd("0.5"), merchant_name="NewsHub", category="data", item="x")
    assert res.mismatch and res.llm_reasons == ()
