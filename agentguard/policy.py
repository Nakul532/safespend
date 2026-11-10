"""The deterministic policy engine. validate_payment() is the only way to get a
SettlementPermit, and the ledger settles nothing without one.

Every check runs so the audit record lists everything that would have failed.
The decision itself uses the first failing check in CHECK_ORDER.
"""
from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import timedelta
from typing import Callable

from .approvals import ApprovalService
from .audit import AuditLog, EventType
from .circuit_breaker import CircuitBreaker
from .clock import Clock, utc_day_start
from .config import PolicyConfig
from .idempotency import IdempotencyStore
from .ledger import Ledger
from .lookalike import find_lookalike
from .models import (
    Agent,
    AgentStatus,
    CheckResult,
    Decision,
    Merchant,
    Outcome,
    PaymentRequest,
    SettlementPermit,
)
from .money import fmt_usd
from .reason_codes import ReasonCode
from .registry import Registry
from .sanctions import SanctionsScreener
from .signing import Signer

# Approval failures that leave the payment waiting for a (new) human approval.
_WAITS_FOR_APPROVAL = {ReasonCode.APPROVAL_REQUIRED, ReasonCode.APPROVAL_EXPIRED}


class _Ctx:
    """Everything one evaluation needs, computed once."""

    def __init__(self, engine: "PolicyEngine", req: PaymentRequest) -> None:
        self.req = req
        self.now = engine.clock.now()
        self.agent: Agent | None = engine.registry.agents.get(req.agent_id)
        self.merchant: Merchant | None = engine.registry.merchants.get(req.merchant_id)
        day = utc_day_start(self.now)
        self.today = engine.ledger.payments(since=day)
        self.recent = engine.ledger.payments(since=self.now - timedelta(hours=engine.config.invoice_duplicate_window_hours))


Check = Callable[["PolicyEngine", _Ctx], CheckResult | None]


class PolicyEngine:
    def __init__(
        self,
        *,
        clock: Clock,
        config: PolicyConfig,
        registry: Registry,
        ledger: Ledger,
        audit: AuditLog,
        approvals: ApprovalService,
        breaker: CircuitBreaker,
        sanctions: SanctionsScreener,
        permit_signer: Signer,
    ) -> None:
        self.clock = clock
        self.config = config
        self.registry = registry
        self.ledger = ledger
        self.audit = audit
        self.approvals = approvals
        self.breaker = breaker
        self.sanctions = sanctions
        self._signer = permit_signer
        self.idempotency = IdempotencyStore()
        self._seq = itertools.count(1)

    # -- checks, in order ---------------------------------------------------

    def _breaker(self, c: _Ctx) -> CheckResult | None:
        if self.breaker.is_open:
            return CheckResult(ReasonCode.CIRCUIT_BREAKER_OPEN, f"all spending paused: {self.breaker.trip_reason}")
        return None

    def _agent_known(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return CheckResult(ReasonCode.AGENT_UNKNOWN, f"agent {c.req.agent_id} is not registered")
        return None

    def _agent_active(self, c: _Ctx) -> CheckResult | None:
        if c.agent is not None and c.agent.status is not AgentStatus.ACTIVE:
            return CheckResult(ReasonCode.AGENT_SUSPENDED, f"agent {c.agent.agent_id} is {c.agent.status}")
        return None

    def _amount(self, c: _Ctx) -> CheckResult | None:
        if c.req.currency != "USD":
            return CheckResult(ReasonCode.INVALID_AMOUNT, f"unsupported currency {c.req.currency}")
        if not isinstance(c.req.amount, int) or isinstance(c.req.amount, bool) or c.req.amount <= 0:
            return CheckResult(ReasonCode.INVALID_AMOUNT, "amount must be a positive whole number of micro-dollars")
        return None

    def _merchant_known(self, c: _Ctx) -> CheckResult | None:
        if c.merchant is None:
            return CheckResult(ReasonCode.MERCHANT_UNKNOWN, f"merchant {c.req.merchant_id} is not registered")
        return None

    def _lookalike(self, c: _Ctx) -> CheckResult | None:
        if c.merchant is None or (c.agent is not None and c.merchant.merchant_id in c.agent.allowed_merchants):
            return None
        m = find_lookalike(c.merchant, self.registry.trusted_merchants(), self.config.lookalike_max_distance)
        if m is not None:
            return CheckResult(
                ReasonCode.LOOKALIKE_MERCHANT,
                f"'{m.merchant_name}' resembles trusted merchant '{m.resembles_name}' (edit distance {m.distance})",
            )
        return None

    def _allowlist(self, c: _Ctx) -> CheckResult | None:
        if c.agent is not None and c.req.merchant_id not in c.agent.allowed_merchants:
            return CheckResult(ReasonCode.MERCHANT_NOT_ALLOWLISTED, f"{c.req.merchant_id} is not on {c.agent.agent_id}'s allowlist")
        return None

    def _sanctions(self, c: _Ctx) -> CheckResult | None:
        if c.merchant is None:
            return None
        hit = self.sanctions.screen(c.merchant.name)
        if hit is not None:
            return CheckResult(
                ReasonCode.SANCTIONS_HIT,
                f"'{hit.screened_name}' matches '{hit.listed_name}' on {hit.list_name} ({hit.list_date})",
            )
        return None

    def _per_txn(self, c: _Ctx) -> CheckResult | None:
        if c.agent is not None and c.req.amount > c.agent.per_txn_limit:
            return CheckResult(
                ReasonCode.PER_TXN_LIMIT_EXCEEDED,
                f"{fmt_usd(c.req.amount)} is over the per-payment limit of {fmt_usd(c.agent.per_txn_limit)}",
            )
        return None

    def _merchant_limit(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return None
        limit = c.agent.merchant_limit(c.req.merchant_id)
        if limit is None:
            return None
        spent = sum(t.amount for t in c.today if t.agent_id == c.agent.agent_id and t.merchant_id == c.req.merchant_id)
        if spent + c.req.amount > limit:
            return CheckResult(
                ReasonCode.MERCHANT_LIMIT_EXCEEDED,
                f"{fmt_usd(spent)} already spent at {c.req.merchant_id} today; {fmt_usd(c.req.amount)} more exceeds {fmt_usd(limit)}",
            )
        return None

    def _budget(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return None
        spent = sum(t.amount for t in c.today if t.agent_id == c.agent.agent_id)
        if spent + c.req.amount > c.agent.daily_budget:
            return CheckResult(
                ReasonCode.BUDGET_EXCEEDED,
                f"{fmt_usd(spent)} spent today; {fmt_usd(c.req.amount)} more exceeds the daily budget of {fmt_usd(c.agent.daily_budget)}",
            )
        return None

    def _owner_budget(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return None
        limit = self.config.owner_daily_budgets.get(c.agent.owner_id)
        if limit is None:
            return None
        spent = sum(t.amount for t in c.today if t.owner_id == c.agent.owner_id)
        if spent + c.req.amount > limit:
            return CheckResult(
                ReasonCode.OWNER_BUDGET_EXCEEDED,
                f"owner {c.agent.owner_id}'s agents spent {fmt_usd(spent)} today; {fmt_usd(c.req.amount)} more exceeds the team budget of {fmt_usd(limit)}",
            )
        return None

    def _velocity(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return None
        since = c.now - timedelta(seconds=self.config.velocity_window_seconds)
        n = sum(1 for t in c.recent if t.agent_id == c.agent.agent_id and t.timestamp > since)
        if n >= c.agent.max_payments_per_window:
            return CheckResult(
                ReasonCode.VELOCITY_EXCEEDED,
                f"{n} payments in the last {self.config.velocity_window_seconds}s; limit is {c.agent.max_payments_per_window}",
            )
        return None

    def _owner_velocity(self, c: _Ctx) -> CheckResult | None:
        cap = self.config.owner_max_payments_per_window
        if c.agent is None or cap is None:
            return None
        since = c.now - timedelta(seconds=self.config.velocity_window_seconds)
        n = sum(1 for t in c.recent if t.owner_id == c.agent.owner_id and t.timestamp > since)
        if n >= cap:
            return CheckResult(
                ReasonCode.OWNER_VELOCITY_EXCEEDED,
                f"owner {c.agent.owner_id}'s agents made {n} payments in the last {self.config.velocity_window_seconds}s; limit is {cap}",
            )
        return None

    def _duplicate(self, c: _Ctx) -> CheckResult | None:
        """Backup heuristic for duplicates that arrive under a new idempotency key."""
        r = c.req
        short = c.now - timedelta(seconds=self.config.duplicate_window_seconds)
        for t in c.recent:
            if t.agent_id != r.agent_id or t.merchant_id != r.merchant_id or t.amount != r.amount:
                continue
            if t.idempotency_key == r.idempotency_key:
                continue
            if r.invoice_ref is not None and t.invoice_ref == r.invoice_ref:
                return CheckResult(ReasonCode.DUPLICATE_SUSPECTED, f"invoice {r.invoice_ref} was already paid in {t.txn_id}")
            if r.invoice_ref is None and t.invoice_ref is None and t.timestamp > short:
                return CheckResult(
                    ReasonCode.DUPLICATE_SUSPECTED,
                    f"same agent, merchant and amount as {t.txn_id} within {self.config.duplicate_window_seconds}s",
                )
        return None

    def _funds(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None:
            return None
        bal = self.ledger.balance(c.agent.wallet_account)
        if bal < c.req.amount:
            return CheckResult(ReasonCode.INSUFFICIENT_FUNDS, f"wallet holds {fmt_usd(bal)}; payment needs {fmt_usd(c.req.amount)}")
        return None

    def _approval(self, c: _Ctx) -> CheckResult | None:
        if c.agent is None or c.req.amount < c.agent.approval_threshold:
            return None
        return self.approvals.check(c.req)

    CHECK_ORDER: tuple[tuple[str, Check], ...] = (
        ("circuit_breaker", _breaker),
        ("agent_known", _agent_known),
        ("agent_active", _agent_active),
        ("amount_valid", _amount),
        ("merchant_known", _merchant_known),
        ("lookalike_merchant", _lookalike),
        ("merchant_allowlist", _allowlist),
        ("sanctions", _sanctions),
        ("per_txn_limit", _per_txn),
        ("merchant_daily_limit", _merchant_limit),
        ("agent_daily_budget", _budget),
        ("owner_daily_budget", _owner_budget),
        ("agent_velocity", _velocity),
        ("owner_velocity", _owner_velocity),
        ("duplicate_heuristic", _duplicate),
        ("sufficient_funds", _funds),
        ("human_approval", _approval),
    )

    # -- the one entry point ------------------------------------------------

    def _new_decision_id(self) -> str:
        return f"D{next(self._seq):07d}"

    def _audit_decision(self, req: PaymentRequest, d: Decision, skipped: list[str] | None = None) -> None:
        self.audit.append(
            EventType.DECISION,
            {
                "decision_id": d.decision_id,
                "outcome": d.outcome,
                "reason_code": d.reason_code,
                "failed_checks": [{"code": f.code, "detail": f.detail} for f in d.failed_checks],
                "checks_evaluated": list(d.checks_evaluated),
                "checks_skipped": skipped or [],
                "request": {**req.financial_fields(), "description": req.description,
                            "approval_id": req.approval.approval_id if req.approval else None},
                "payment_hash": d.payment_hash,
                "policy_hash": d.policy_hash,
            },
            d.policy_version,
        )

    def _blocked(self, req: PaymentRequest, code: ReasonCode, detail: str, evaluated: tuple[str, ...]) -> Decision:
        d = Decision(
            decision_id=self._new_decision_id(),
            outcome=Outcome.BLOCKED,
            reason_code=code,
            failed_checks=(CheckResult(code, detail),),
            checks_evaluated=evaluated,
            payment_hash=req.payment_hash,
            policy_version=self.config.version,
            policy_hash=self.config.config_hash,
            decided_at=self.clock.now(),
        )
        self._audit_decision(req, d)
        return d

    def validate_payment(self, req: PaymentRequest) -> Decision:
        # 1. Idempotency key: required, and the primary duplicate/replay defence.
        if not req.idempotency_key or not req.idempotency_key.strip():
            return self._blocked(req, ReasonCode.MISSING_IDEMPOTENCY_KEY, "every payment request needs an idempotency key", ("idempotency_key",))
        stored = self.idempotency.get(req.agent_id, req.idempotency_key)
        if stored is not None:
            if stored.payment_hash != req.payment_hash:
                return self._blocked(
                    req, ReasonCode.IDEMPOTENCY_CONFLICT,
                    f"key already used for a different payment ({stored.decision.decision_id})", ("idempotency_key",),
                )
            if stored.decision.outcome is not Outcome.PENDING_APPROVAL:
                self.audit.append(
                    EventType.IDEMPOTENT_REPLAY,
                    {"original_decision_id": stored.decision.decision_id, "payment_hash": req.payment_hash,
                     "outcome": stored.decision.outcome},
                    self.config.version,
                )
                # Return the original result. The permit is stripped: it was already used or never existed.
                return replace(stored.decision, replayed=True, permit=None)
            # A pending payment is re-evaluated, usually now carrying its approval.

        # 2. Run every check; record all failures.
        c = _Ctx(self, req)
        failures: list[CheckResult] = []
        evaluated: list[str] = []
        for name, check in self.CHECK_ORDER:
            evaluated.append(name)
            result = check(self, c)
            if result is not None:
                failures.append(result)

        # 3. Decide on the first failure.
        if not failures:
            outcome, reason = Outcome.APPROVED, ReasonCode.APPROVED
        elif failures[0].code in _WAITS_FOR_APPROVAL:
            outcome, reason = Outcome.PENDING_APPROVAL, failures[0].code
        else:
            outcome, reason = Outcome.BLOCKED, failures[0].code

        decision_id = self._new_decision_id()
        permit = None
        if outcome is Outcome.APPROVED:
            draft = SettlementPermit(decision_id, req.payment_hash, req.agent_id, req.merchant_id, req.amount, "")
            permit = replace(draft, signature=self._signer.sign(draft.signed_fields()))

        d = Decision(
            decision_id=decision_id,
            outcome=outcome,
            reason_code=reason,
            failed_checks=tuple(failures),
            checks_evaluated=tuple(evaluated),
            payment_hash=req.payment_hash,
            policy_version=self.config.version,
            policy_hash=self.config.config_hash,
            decided_at=c.now,
            permit=permit,
        )
        self._audit_decision(req, d)
        self.idempotency.put(req.agent_id, req.idempotency_key, req.payment_hash, d)
        if outcome is Outcome.PENDING_APPROVAL:
            self.approvals.register_pending(req, decision_id)
        return d
