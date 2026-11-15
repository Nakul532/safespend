"""Maker-checker approvals bound to one exact payment.

- Only payments the PolicyEngine marked PENDING_APPROVAL can be approved.
- The approver must be a registered human approver, not the agent's owner
  and not the agent itself (segregation of duties).
- The approval is signed over agent, merchant, amount, payment hash and
  expiry. An altered, expired, mismatched or reused approval is rejected.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from datetime import timedelta

from .audit import AuditLog, EventType
from .clock import Clock
from .models import Approval, CheckResult, PaymentRequest
from .reason_codes import ReasonCode
from .registry import Registry
from .signing import Signer


class ApprovalError(Exception):
    pass


@dataclass
class _Pending:
    request: PaymentRequest
    decision_id: str


class ApprovalService:
    def __init__(
        self,
        clock: Clock,
        signer: Signer,
        registry: Registry,
        audit: AuditLog,
        policy_version: str,
        ttl_seconds: int,
    ) -> None:
        self._clock = clock
        self._signer = signer
        self._registry = registry
        self._audit = audit
        self._policy_version = policy_version
        self._ttl = ttl_seconds
        self._pending: dict[str, _Pending] = {}  # payment_hash -> pending request
        self._issued: dict[str, Approval] = {}
        self._consumed: dict[str, str] = {}  # approval_id -> txn_id
        self._seq = itertools.count(1)

    def register_pending(self, request: PaymentRequest, decision_id: str) -> None:
        self._pending[request.payment_hash] = _Pending(request, decision_id)

    def _refuse(self, payment_hash: str, approver_id: str, why: str) -> ApprovalError:
        self._audit.append(
            EventType.APPROVAL_REFUSED,
            {"payment_hash": payment_hash, "approver_id": approver_id, "reason": why},
            self._policy_version,
        )
        return ApprovalError(why)

    def grant(self, payment_hash: str, approver_id: str, ttl_seconds: int | None = None) -> Approval:
        pending = self._pending.get(payment_hash)
        if pending is None:
            raise self._refuse(payment_hash, approver_id, "no payment is waiting for approval with this hash")
        req = pending.request
        agent = self._registry.agents[req.agent_id]
        if approver_id in self._registry.agents:
            raise self._refuse(payment_hash, approver_id, "agents cannot approve payments")
        if approver_id not in self._registry.approvers:
            raise self._refuse(payment_hash, approver_id, "approver is not a registered human approver")
        if approver_id == agent.owner_id:
            raise self._refuse(payment_hash, approver_id, "the agent's owner cannot approve its payments (four-eyes)")

        now = self._clock.now()
        ttl = self._ttl if ttl_seconds is None else ttl_seconds
        unsigned = dict(
            approval_id=f"APR{next(self._seq):06d}",
            payment_hash=payment_hash,
            agent_id=req.agent_id,
            merchant_id=req.merchant_id,
            amount=req.amount,
            approver_id=approver_id,
            granted_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        draft = Approval(**unsigned, signature="")
        approval = Approval(**unsigned, signature=self._signer.sign(draft.signed_fields()))
        self._issued[approval.approval_id] = approval
        del self._pending[payment_hash]
        self._audit.append(
            EventType.APPROVAL_GRANTED,
            {**approval.signed_fields(), "pending_decision_id": pending.decision_id},
            self._policy_version,
        )
        return approval

    def check(self, request: PaymentRequest) -> CheckResult | None:
        """Return a failing CheckResult, or None if the attached approval is valid."""
        a = request.approval
        if a is None:
            return CheckResult(ReasonCode.APPROVAL_REQUIRED, "payment is at or above the approval threshold")
        if not self._signer.verify(a.signed_fields(), a.signature):
            return CheckResult(ReasonCode.APPROVAL_INVALID, "approval signature does not match: approval was altered or forged")
        if self._issued.get(a.approval_id) != a:
            return CheckResult(ReasonCode.APPROVAL_INVALID, "approval was not issued by this system")
        if (
            a.payment_hash != request.payment_hash
            or a.amount != request.amount
            or a.merchant_id != request.merchant_id
            or a.agent_id != request.agent_id
        ):
            return CheckResult(ReasonCode.APPROVAL_INVALID, "approval is bound to a different payment")
        if a.approval_id in self._consumed:
            return CheckResult(ReasonCode.APPROVAL_REUSED, f"approval already used for {self._consumed[a.approval_id]}")
        if self._clock.now() >= a.expires_at:
            return CheckResult(ReasonCode.APPROVAL_EXPIRED, f"approval expired at {a.expires_at.isoformat()}")
        return None

    def consume(self, approval_id: str, txn_id: str) -> None:
        self._consumed[approval_id] = txn_id
