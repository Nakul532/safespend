"""Runs AgentGuard inside the red-team runner. ADDED AFTER THE RED-TEAM LOCK (Stage 3).

Each config is a set of switches, so every after-lock addition can be
reported with and without it.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal

from agentguard import AgentGuard, PaymentRequest, usd
from agentguard.approvals import ApprovalError
from agentguard.clock import ManualClock
from agentguard.models import Agent, Merchant, Outcome
from agentguard.registry import Registry
from agentguard.sanctions import ExactListScreener, FuzzyScreener


@dataclass(frozen=True)
class Config:
    name: str
    price_check: bool = False  # added after lock
    fuzzy_sanctions: bool = False  # added after lock (Stage 1 had exact matching only)
    injection: bool = False  # added after lock
    aml_monitoring: bool = False  # Stage 1 monitor, run after every payment; flags only
    aml_hold_severity: int | None = None  # added after lock: alerts at/above this hold the agent
    run_tag: str = "run1"  # separates repeated LLM runs in the cache
    split_check: bool = False  # added after Stage 3 results (round 2)
    lookalike_hold_min_trusted: int | None = None  # added after Stage 3 results (round 2)
    commitment_check: bool = False  # added after lock (Stage 4)

    @property
    def after_lock(self) -> list[str]:
        out = []
        if self.price_check:
            out.append("quoted-vs-charged price check")
        if self.fuzzy_sanctions:
            out.append("fuzzy sanctions screening")
        if self.injection:
            out.append("injection check (heuristics + LLM)")
        if self.aml_hold_severity is not None:
            out.append(f"AML->hold at severity {self.aml_hold_severity}")
        if self.split_check:
            out.append("pre-payment split check")
        if self.lookalike_hold_min_trusted is not None:
            out.append(f"look-alike holds with >= {self.lookalike_hold_min_trusted} trusted merchants")
        if self.commitment_check:
            out.append("recurring-commitment and stored-credential holds")
        return out


@dataclass
class StepStat:
    scenario: str
    step: int
    total_ms: float
    llm_called: bool
    llm_ms: float | None
    outside_content: bool
    llm_cached: bool = False


@dataclass
class Stats:
    steps: list[StepStat] = field(default_factory=list)


def build_registry(world: dict) -> Registry:
    reg = Registry()
    for m in world["merchants"]:
        reg.add_merchant(Merchant(m["id"], m["name"], m["category"], trusted=bool(m.get("trusted"))))
    for a in world["agents"]:
        reg.add_agent(Agent(
            agent_id=a["id"], name=a["id"], role=a.get("role", ""), owner_id=a["owner"],
            per_txn_limit=usd(a["per_payment_limit_usd"]), daily_budget=usd(a["daily_budget_usd"]),
            approval_threshold=usd(a["approval_threshold_usd"]), allowed_merchants=frozenset(a["allowlist"]),
        ))
    reg.approvers |= set(world["approvers"])
    return reg


class AgentGuardAdapter:
    def __init__(self, config: Config, checker=None, stats: Stats | None = None) -> None:
        self.config = config
        self.name = config.name
        self.checker = checker if config.injection else None
        self.stats = stats if stats is not None else Stats()

    def reset(self, world: dict, scenario: dict, start_time: datetime) -> None:
        from agentguard.config import PolicyConfig
        self.scenario_id = scenario["id"]
        self.clock = ManualClock(start_time)
        reg = build_registry(world)
        sl = world["sanctions_list"]
        screener = (FuzzyScreener if self.config.fuzzy_sanctions else ExactListScreener)(
            sl["entries"], list_name=sl["name"], list_date=sl["list_date"])
        version = "policy-2026.11.10-1" + ("+after-lock:" + ",".join(self.config.after_lock) if self.config.after_lock else "")
        self.guard = AgentGuard(reg, clock=self.clock, policy=PolicyConfig(version=version, price_check=self.config.price_check,
                                                                    split_check=self.config.split_check,
                                                                    lookalike_hold_min_trusted=self.config.lookalike_hold_min_trusted,
                                                                    commitment_check=self.config.commitment_check),
                                sanctions=screener, injection_checker=self.checker,
                                aml_hold_severity=self.config.aml_hold_severity)
        for a in reg.agents.values():
            self.guard.fund(a.agent_id, a.daily_budget * 10)  # funds never limit a scenario
        self.requests: dict[int, PaymentRequest] = {}
        self.grants: dict[tuple[int, str], object] = {}
        self.txn_step: dict[str, int] = {}
        self.start = start_time

    def _approval(self, step: dict, req: PaymentRequest, now: datetime):
        ap = step.get("approval")
        if not ap:
            return None
        key = (ap["for_step"], ap["approver"])
        if key not in self.grants:
            target = req if ap["for_step"] == step["step"] else self.requests.get(ap["for_step"])
            expires_offset = ap["issued_offset_seconds"] + ap["ttl_seconds"]
            ttl = expires_offset - int((now - self.start).total_seconds())
            try:
                # The named person tries to approve; the guard refuses self-approval, strangers
                # and payments that were never held.
                self.grants[key] = self.guard.grant_approval(target.payment_hash, ap["approver"], ttl_seconds=ttl)
            except (ApprovalError, AttributeError):
                self.grants[key] = None
        return self.grants[key]

    def submit(self, step: dict, now: datetime) -> dict:
        self.clock.set(now)
        q = step.get("quoted_amount_usd")
        req = PaymentRequest(
            agent_id=step["agent"], merchant_id=step["merchant"], amount=usd(Decimal(step["amount_usd"])),
            idempotency_key=step["idempotency_key"], invoice_ref=step.get("invoice_ref"),
            description=(step.get("context") or {}).get("task") or "",
            quoted_amount=usd(Decimal(q)) if q is not None else None, context=step.get("context") or {},
        )
        req = replace(req, approval=self._approval(step, req, now))
        self.requests[step["step"]] = req
        t0 = time.perf_counter()
        d = self.guard.submit_payment(req)
        total_ms = (time.perf_counter() - t0) * 1000
        inj = self.guard.engine.last_injection if not d.replayed else None
        from agentguard.injection import has_outside_content
        self.stats.steps.append(StepStat(self.scenario_id, step["step"], total_ms, bool(inj and inj.llm_called),
                                         inj.llm_latency_ms if inj else None, has_outside_content(req.context or {}),
                                         bool(inj and inj.llm_cached)))
        if d.txn_id:
            self.txn_step[d.txn_id] = step["step"]
        if self.config.aml_monitoring:
            self.guard.run_monitoring()
        if d.outcome is Outcome.APPROVED:
            return {"decision": "allow", "charged": bool(d.txn_id) and not d.replayed, "reason": str(d.reason_code)}
        return {"decision": "hold" if d.outcome is Outcome.PENDING_APPROVAL else "block", "charged": False,
                "reason": str(d.reason_code)}

    def flags(self, now: datetime) -> list[dict]:
        if not self.config.aml_monitoring:
            return []
        out = []
        for a in self.guard.monitor.alerts.values():
            steps = [self.txn_step[t] for t in a.txn_ids if t in self.txn_step]
            if steps:
                out.append({"steps": steps, "at": a.raised_at, "rule": str(a.rule), "severity": a.severity})
        return out
