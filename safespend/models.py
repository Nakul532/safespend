"""Core records: agents, merchants, payment requests, approvals, decisions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from .reason_codes import ReasonCode


def canonical_json(data: Any) -> str:
    """Stable JSON used for every hash in the system."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def sha256_hex(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    name: str
    category: str
    # Trusted merchants are the reference set for look-alike detection.
    trusted: bool = True


class AgentStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class Agent:
    agent_id: str
    name: str
    role: str
    owner_id: str  # the human or team accountable for this agent
    per_txn_limit: int  # micro-dollars
    daily_budget: int  # micro-dollars, resets at 00:00 UTC
    approval_threshold: int  # payments >= this need a human approver
    allowed_merchants: frozenset[str]
    # Per-merchant daily caps. Merchants not listed use default_merchant_daily_limit.
    merchant_daily_limits: Mapping[str, int] = field(default_factory=dict)
    default_merchant_daily_limit: int | None = None
    max_payments_per_window: int = 20  # velocity limit (window set in PolicyConfig)
    status: AgentStatus = AgentStatus.ACTIVE

    @property
    def wallet_account(self) -> str:
        return f"wallet:{self.agent_id}"

    def merchant_limit(self, merchant_id: str) -> int | None:
        return self.merchant_daily_limits.get(merchant_id, self.default_merchant_daily_limit)


@dataclass(frozen=True)
class Approval:
    """A human approval bound to one exact payment.

    The signature covers every field, so editing any of them (amount,
    merchant, payment hash, expiry) makes the approval invalid.
    """

    approval_id: str
    payment_hash: str
    agent_id: str
    merchant_id: str
    amount: int
    approver_id: str
    granted_at: datetime
    expires_at: datetime
    signature: str

    def signed_fields(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "payment_hash": self.payment_hash,
            "agent_id": self.agent_id,
            "merchant_id": self.merchant_id,
            "amount": self.amount,
            "approver_id": self.approver_id,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass(frozen=True)
class Commitment:
    """A future charge the payment sets up. ADDED AFTER LOCK (Stage 4)."""
    kind: str  # recurring | trial_conversion | auto_topup
    amount_per_period: int | None = None  # micro-dollars
    period_days: int | None = None


@dataclass(frozen=True)
class PaymentRequest:
    agent_id: str
    merchant_id: str
    amount: int  # micro-dollars
    idempotency_key: str
    currency: str = "USD"
    invoice_ref: str | None = None
    description: str = ""
    approval: Approval | None = None
    # Stage 3 (added after lock): what the agent was shown. Not part of the payment hash.
    quoted_amount: int | None = field(default=None, compare=False)
    context: Mapping[str, Any] | None = field(default=None, compare=False)
    # Stage 4 (added after lock): future commitments. Part of the payment hash only when set,
    # so an approval covers the terms it was granted for and older hashes are unchanged.
    commitment: Commitment | None = None
    store_credential: bool = False
    # Stage 4 (added after lock): what the person originally asked for (safespend.intent.Intent).
    # Not part of the payment hash: it describes the request, not the money movement.
    intent: Any = field(default=None, compare=False)

    def financial_fields(self) -> dict[str, Any]:
        """The fields that define 'the same payment'. Description and approval are excluded."""
        return {
            "agent_id": self.agent_id,
            "merchant_id": self.merchant_id,
            "amount": self.amount,
            "currency": self.currency,
            "idempotency_key": self.idempotency_key,
            "invoice_ref": self.invoice_ref,
        } | ({"commitment": {"kind": self.commitment.kind, "amount_per_period": self.commitment.amount_per_period,
                             "period_days": self.commitment.period_days}} if self.commitment else {}) \
          | ({"store_credential": True} if self.store_credential else {})

    @property
    def payment_hash(self) -> str:
        return sha256_hex(self.financial_fields())


class Outcome(StrEnum):
    APPROVED = "APPROVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CheckResult:
    code: ReasonCode
    detail: str


@dataclass(frozen=True)
class SettlementPermit:
    """Proof that validate_payment() approved this exact payment.

    Only the PolicyEngine can sign one; the Ledger refuses anything else.
    """

    decision_id: str
    payment_hash: str
    agent_id: str
    merchant_id: str
    amount: int
    signature: str

    def signed_fields(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "payment_hash": self.payment_hash,
            "agent_id": self.agent_id,
            "merchant_id": self.merchant_id,
            "amount": self.amount,
        }


@dataclass(frozen=True)
class Decision:
    decision_id: str
    outcome: Outcome
    reason_code: ReasonCode  # the first failing check, or APPROVED
    failed_checks: tuple[CheckResult, ...]  # every check that failed, in order
    checks_evaluated: tuple[str, ...]
    payment_hash: str
    policy_version: str
    policy_hash: str
    decided_at: datetime
    permit: SettlementPermit | None = None
    replayed: bool = False
    txn_id: str | None = None  # set once the ledger settles the payment

    @property
    def approved(self) -> bool:
        return self.outcome is Outcome.APPROVED
