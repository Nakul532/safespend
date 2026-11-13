"""AgentGuard: wires the policy engine, ledger, approvals, breaker, audit log and AML.

submit_payment() is the normal entry point. It calls validate_payment()
and settles only an APPROVED decision, using that decision's permit.
"""
from __future__ import annotations

from dataclasses import replace

from .aml import Alert, AmlConfig, AmlMonitor
from .approvals import ApprovalService
from .audit import AuditLog, EventType, VerifyResult
from .circuit_breaker import CircuitBreaker
from .clock import Clock, SystemClock
from .config import BreakerConfig, PolicyConfig
from .ledger import Ledger, LedgerTxn
from .models import Approval, Decision, PaymentRequest
from .policy import PolicyEngine
from .registry import Registry
from .sanctions import NullScreener, SanctionsScreener
from .signing import Signer


class AgentGuard:
    def __init__(
        self,
        registry: Registry,
        *,
        clock: Clock | None = None,
        policy: PolicyConfig | None = None,
        breaker: BreakerConfig | None = None,
        aml: AmlConfig | None = None,
        sanctions: SanctionsScreener | None = None,
        injection_checker=None,
        aml_hold_severity: int | None = None,
    ) -> None:
        self.clock = clock or SystemClock()
        self.registry = registry
        self.policy_config = policy or PolicyConfig()
        version = self.policy_config.version
        permit_signer = Signer()
        self.audit = AuditLog(self.clock)
        self.ledger = Ledger(self.clock, permit_signer)
        self.approvals = ApprovalService(
            self.clock, Signer(), registry, self.audit, version, self.policy_config.approval_ttl_seconds
        )
        self.breaker = CircuitBreaker(self.clock, breaker or BreakerConfig(), registry, self.audit, version)
        self.engine = PolicyEngine(
            clock=self.clock,
            config=self.policy_config,
            registry=registry,
            ledger=self.ledger,
            audit=self.audit,
            approvals=self.approvals,
            breaker=self.breaker,
            sanctions=sanctions or NullScreener(),
            permit_signer=permit_signer,
            injection_checker=injection_checker,
        )
        # Added after lock: AML alerts at or above this severity hold the agents involved.
        self.aml_hold_severity = aml_hold_severity
        self.monitor = AmlMonitor(registry, aml)
        self._decision_txn: dict[str, str] = {}

    # -- payments -----------------------------------------------------------

    def validate_payment(self, request: PaymentRequest) -> Decision:
        return self.engine.validate_payment(request)

    def submit_payment(self, request: PaymentRequest) -> Decision:
        decision = self.engine.validate_payment(request)
        if decision.replayed:
            return replace(decision, txn_id=self._decision_txn.get(decision.decision_id))
        if not decision.approved:
            return decision
        agent = self.registry.agents[request.agent_id]
        approval_valid = request.approval is not None and self.approvals.check(request) is None
        txn = self.ledger.settle(decision.permit, request, agent)
        if approval_valid:
            self.approvals.consume(request.approval.approval_id, txn.txn_id)
        self._decision_txn[decision.decision_id] = txn.txn_id
        self.audit.append(
            EventType.SETTLED,
            {"decision_id": decision.decision_id, "txn_id": txn.txn_id, "amount": txn.amount,
             "agent_id": txn.agent_id, "merchant_id": txn.merchant_id, "simulated": True},
            self.policy_config.version,
        )
        self.breaker.evaluate_spend(self.ledger)
        return replace(decision, txn_id=txn.txn_id)

    def fund(self, agent_id: str, amount: int) -> LedgerTxn:
        return self.ledger.fund(self.registry.agents[agent_id], amount)

    # -- humans -------------------------------------------------------------

    def grant_approval(self, payment_hash: str, approver_id: str, ttl_seconds: int | None = None) -> Approval:
        return self.approvals.grant(payment_hash, approver_id, ttl_seconds)

    def resume_spending(self, approver_id: str) -> None:
        self.breaker.resume(approver_id)

    # -- monitoring ---------------------------------------------------------

    def run_monitoring(self) -> list[Alert]:
        new = self.monitor.scan_ledger(self.ledger)
        for a in new:
            self.audit.append(
                EventType.AML_ALERT,
                {"alert_id": a.alert_id, "rule": a.rule, "severity": a.severity, "subject_type": a.subject_type,
                 "subject_id": a.subject_id, "txn_ids": list(a.txn_ids), "facts": a.facts},
                self.policy_config.version,
            )
        self.breaker.evaluate_alerts(self.monitor.alerts.values(), self.ledger)
        if self.aml_hold_severity is not None:
            for a in new:
                if a.severity >= self.aml_hold_severity:
                    for tid in a.txn_ids:
                        t = self.ledger.get(tid)
                        if t is not None:
                            self.engine.aml_holds.add(t.agent_id)
        return new

    def verify_audit_log(self) -> VerifyResult:
        return self.audit.verify()
