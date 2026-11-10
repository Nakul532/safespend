"""Idempotency keys, maker-checker approvals, and the single path to settlement."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from agentguard import Outcome, ReasonCode as R, usd
from agentguard.approvals import ApprovalError
from agentguard.audit import EventType
from agentguard.ledger import LedgerError
from agentguard.models import SettlementPermit
from conftest import OWNER_GROWTH, OWNER_MARKETS, RISK_OFFICER, req

# == idempotency (primary duplicate / replay defence) ==========================


def test_missing_key_blocked(guard):
    for k in ("", "   "):
        assert guard.submit_payment(req(idempotency_key=k)).reason_code is R.MISSING_IDEMPOTENCY_KEY


def test_present_key_passes(guard):
    assert guard.submit_payment(req(idempotency_key="k-1")).approved


def test_replay_same_key_same_payment_charges_once(guard, clock):
    first = guard.submit_payment(req(idempotency_key="k-1"))
    clock.advance(hours=2)  # long after the duplicate-heuristic window
    again = guard.submit_payment(req(idempotency_key="k-1"))
    assert again.replayed and again.decision_id == first.decision_id and again.txn_id == first.txn_id
    assert again.permit is None
    assert len(guard.ledger.payments()) == 1
    assert len(guard.audit.by_type(EventType.IDEMPOTENT_REPLAY)) == 1


def test_replay_of_blocked_returns_original_block(guard):
    first = guard.submit_payment(req(merchant="m_pixelmint", idempotency_key="k-b"))
    again = guard.submit_payment(req(merchant="m_pixelmint", idempotency_key="k-b"))
    assert again.replayed and again.reason_code is R.MERCHANT_NOT_ALLOWLISTED
    assert again.decision_id == first.decision_id


def test_same_key_different_payment_is_conflict(guard):
    guard.submit_payment(req(amount=usd("0.002"), idempotency_key="k-1"))
    d = guard.submit_payment(req(amount=usd("0.003"), idempotency_key="k-1"))
    assert d.reason_code is R.IDEMPOTENCY_CONFLICT and not d.replayed
    assert len(guard.ledger.payments()) == 1


def test_keys_are_scoped_per_agent(guard):
    assert guard.submit_payment(req(agent="agent_001", idempotency_key="shared")).approved
    assert guard.submit_payment(req(agent="agent_003", idempotency_key="shared")).approved


# == approvals (maker-checker) =================================================


def _pending(guard, amount=usd(3), **kw):
    r = req(amount=amount, **kw)
    d = guard.submit_payment(r)
    assert d.outcome is Outcome.PENDING_APPROVAL
    return r, d


def test_approved_payment_settles_and_consumes_approval(guard):
    r, d = _pending(guard)
    approval = guard.grant_approval(d.payment_hash, OWNER_MARKETS)  # not agent_001's owner
    done = guard.submit_payment(replace(r, approval=approval))
    assert done.approved and done.txn_id is not None
    assert guard.approvals.check(replace(r, approval=approval)).code is R.APPROVAL_REUSED


def test_owner_cannot_approve_own_agent(guard):
    _, d = _pending(guard)
    with pytest.raises(ApprovalError, match="four-eyes"):
        guard.grant_approval(d.payment_hash, OWNER_GROWTH)
    assert guard.audit.by_type(EventType.APPROVAL_REFUSED)[-1].payload["approver_id"] == OWNER_GROWTH


def test_agent_cannot_approve(guard):
    _, d = _pending(guard)
    with pytest.raises(ApprovalError, match="agents cannot"):
        guard.grant_approval(d.payment_hash, "agent_002")


def test_unregistered_person_cannot_approve(guard):
    _, d = _pending(guard)
    with pytest.raises(ApprovalError, match="registered"):
        guard.grant_approval(d.payment_hash, "user_random")


def test_cannot_approve_a_payment_that_is_not_pending(guard):
    d = guard.submit_payment(req(amount=usd(1)))
    with pytest.raises(ApprovalError, match="no payment is waiting"):
        guard.grant_approval(d.payment_hash, RISK_OFFICER)


def test_approval_bound_to_amount(guard):
    r, d = _pending(guard, amount=usd(3))
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    bigger = replace(r, amount=usd("4.99"), approval=approval)  # same key, new amount
    assert guard.submit_payment(bigger).reason_code is R.IDEMPOTENCY_CONFLICT
    bigger_new_key = replace(bigger, idempotency_key="other")
    assert guard.submit_payment(bigger_new_key).reason_code is R.APPROVAL_INVALID


def test_approval_bound_to_merchant(guard):
    r, d = _pending(guard, amount=usd(3))
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    moved = replace(r, merchant_id="m_finstream", idempotency_key="other", approval=approval)
    out = guard.submit_payment(moved)
    assert out.reason_code is R.APPROVAL_INVALID and "different payment" in out.failed_checks[0].detail


def test_altered_approval_rejected(guard):
    r, d = _pending(guard)
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    forged = replace(approval, expires_at=approval.expires_at + timedelta(days=30))
    out = guard.submit_payment(replace(r, approval=forged))
    assert out.reason_code is R.APPROVAL_INVALID and out.outcome is Outcome.BLOCKED
    assert "altered" in out.failed_checks[0].detail


def test_expired_approval_rejected_and_can_be_reapproved(guard, clock):
    r, d = _pending(guard)
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER, ttl_seconds=60)
    clock.advance(seconds=61)
    out = guard.submit_payment(replace(r, approval=approval))
    assert out.reason_code is R.APPROVAL_EXPIRED and out.outcome is Outcome.PENDING_APPROVAL
    fresh = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    assert guard.submit_payment(replace(r, approval=fresh)).approved


def test_unexpired_approval_accepted(guard, clock):
    r, d = _pending(guard)
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER, ttl_seconds=60)
    clock.advance(seconds=59)
    assert guard.submit_payment(replace(r, approval=approval)).approved


def test_approval_cannot_be_reused_for_second_payment(guard, clock):
    r, d = _pending(guard)
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    assert guard.submit_payment(replace(r, approval=approval)).approved
    clock.advance(hours=1)
    second = replace(r, idempotency_key="second", approval=approval)
    assert guard.submit_payment(second).reason_code is R.APPROVAL_INVALID
    assert len(guard.ledger.payments()) == 1


def test_approval_still_subject_to_other_checks(guard):
    r, d = _pending(guard, amount=usd(3))
    approval = guard.grant_approval(d.payment_hash, RISK_OFFICER)
    guard.registry.agents["agent_001"] = replace(guard.registry.agents["agent_001"], daily_budget=usd(1))
    assert guard.submit_payment(replace(r, approval=approval)).reason_code is R.BUDGET_EXCEEDED


# == validate_payment() is the only path to settlement =========================


def test_forged_permit_refused(guard):
    r = req()
    fake = SettlementPermit("D9999999", r.payment_hash, r.agent_id, r.merchant_id, r.amount, "0" * 64)
    with pytest.raises(LedgerError, match="validate_payment"):
        guard.ledger.settle(fake, r, guard.registry.agents[r.agent_id])
    assert guard.ledger.payments() == []


def test_permit_cannot_be_used_twice(guard):
    r = req()
    d = guard.validate_payment(r)
    agent = guard.registry.agents[r.agent_id]
    guard.ledger.settle(d.permit, r, agent)
    with pytest.raises(LedgerError, match="already used"):
        guard.ledger.settle(d.permit, r, agent)


def test_permit_cannot_be_moved_to_another_payment(guard):
    r = req(amount=usd("0.002"))
    d = guard.validate_payment(r)
    other = replace(r, amount=usd(4))
    with pytest.raises(LedgerError, match="does not match"):
        guard.ledger.settle(d.permit, other, guard.registry.agents[r.agent_id])


def test_edited_permit_refused(guard):
    r = req(amount=usd("0.002"))
    d = guard.validate_payment(r)
    bigger = replace(r, amount=usd(4))
    edited = replace(d.permit, amount=usd(4), payment_hash=bigger.payment_hash)
    with pytest.raises(LedgerError, match="validate_payment"):
        guard.ledger.settle(edited, bigger, guard.registry.agents[r.agent_id])


def test_blocked_decision_has_no_permit(guard):
    assert guard.validate_payment(req(merchant="m_pixelmint")).permit is None
    assert guard.validate_payment(req(amount=usd(3))).permit is None  # pending approval


def test_every_settled_payment_has_an_approved_decision(guard, clock):
    for i in range(5):
        guard.submit_payment(req(amount=usd("0.001") * (i + 1)))
        clock.advance(seconds=1)
    approved = {r.payload["decision_id"] for r in guard.audit.by_type(EventType.DECISION) if r.payload["outcome"] == "APPROVED"}
    assert {t.decision_id for t in guard.ledger.payments()} <= approved
