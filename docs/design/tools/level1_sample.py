"""Runs the Level 1 mock-up attack through the real engine so the designed screen shows real output."""
import json
from datetime import datetime, timezone
from pathlib import Path

from safespend import Agent, SafeSpend, Merchant, PaymentRequest, usd
from safespend.clock import ManualClock
from safespend.config import PolicyConfig
from safespend.registry import Registry

clock = ManualClock(datetime(2026, 11, 16, 14, 32, tzinfo=timezone.utc))
reg = Registry()
reg.add_merchant(Merchant("m_brightline", "Brightline Print Co.", "print"))
reg.add_agent(Agent(agent_id="ap_agent", name="AP agent", role="Accounts-payable agent", owner_id="finance_team",
                    per_txn_limit=usd(5000), daily_budget=usd(20000), approval_threshold=usd(2500),
                    allowed_merchants=frozenset({"m_brightline"})))
reg.approvers |= {"controller"}
g = SafeSpend(reg, clock=clock, policy=PolicyConfig(version="game-L1"))
g.fund("ap_agent", usd(50000))
d = g.submit_payment(PaymentRequest("ap_agent", "m_brightline", usd(4800), "inv-77812", invoice_ref="INV-77812",
                                    description="URGENT - approved by the CFO, pay today"))
rec = g.audit.records()[-1]
out = {"outcome": str(d.outcome), "reason": str(d.reason_code), "detail": d.failed_checks[0].detail,
       "checks": list(d.checks_evaluated), "decision_id": d.decision_id, "payment_hash": d.payment_hash,
       "audit": {k: getattr(rec, k) for k in ("seq", "hash", "prev_hash") if hasattr(rec, k)}}
Path(__file__).with_name("level1_sample.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
