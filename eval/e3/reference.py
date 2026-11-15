"""Frozen reference case for investigator v4: alert A6c2d42955a (team structuring, daily shift 2026-11-14).

The synthetic-data fix (whole cents, IDs in time order) renames every alert, so this case is frozen as it was
generated before the fix: the alert, every transaction any alert in that shift touched, the full registry, and all
alerts the rules raised in the last 7 days (for cross-alert links). `python -m eval.e3.reference freeze` was run once,
before the fix; `load()` rebuilds the objects.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from agentguard.aml.rules import Alert
from agentguard.ledger import LedgerTxn, Posting, TxnKind
from agentguard.models import Agent, Merchant
from agentguard.reason_codes import ReasonCode
from agentguard.registry import Registry

PATH = Path(__file__).with_name("reference_A6c2d42955a.json")
ALERT_ID, SEED = "A6c2d42955a", 20261114


def freeze() -> None:
    from agentguard.aml.monitor import AmlMonitor
    from agentguard.synth import DAYS, PLANT_DAYS, START, generate
    sh = generate(SEED)
    cutoff = START + timedelta(days=DAYS - PLANT_DAYS)
    pool = [a for a in AmlMonitor(sh.registry).scan(sh.txns) if a.raised_at >= cutoff]
    queue = {a.alert_id for a in sh.alerts}
    assert ALERT_ID in queue
    ids = sorted({t for a in pool for t in a.txn_ids})
    out = {
        "frozen_at": "2026-11-15", "seed": SEED, "alert_id": ALERT_ID, "data": "synth before the whole-cent / ID-order fix",
        "agents": [{k: (v if not isinstance(v, frozenset) else []) for k, v in a.__dict__.items() if k != "merchant_daily_limits"}
                   | {"status": str(a.status)} for a in sh.registry.agents.values()],
        "merchants": [m.__dict__ for m in sh.registry.merchants.values()],
        "txns": [{"txn_id": t.txn_id, "timestamp": t.timestamp.isoformat(), "amount": t.amount, "agent_id": t.agent_id,
                  "owner_id": t.owner_id, "merchant_id": t.merchant_id} for t in (sh.by_id[i] for i in ids)],
        "alerts": [{"alert_id": a.alert_id, "rule": str(a.rule), "severity": a.severity, "subject_type": a.subject_type,
                    "subject_id": a.subject_id, "txn_ids": list(a.txn_ids), "raised_at": a.raised_at.isoformat(),
                    "explanation": a.explanation, "in_queue": a.alert_id in queue} for a in pool],
    }
    PATH.write_text(json.dumps(out, indent=1))
    print(f"froze {ALERT_ID}: {len(out['txns'])} txns, {len(out['alerts'])} alerts")


def load():
    """Returns (alert, txns_by_id, registry, pool_alerts, queue_ids)."""
    d = json.loads(PATH.read_text())
    reg = Registry()
    for m in d["merchants"]:
        reg.add_merchant(Merchant(**m))
    for a in d["agents"]:
        a = dict(a)
        a.pop("status", None)
        a["allowed_merchants"] = frozenset(reg.merchants)
        reg.add_agent(Agent(**a))
    by_id = {}
    for t in d["txns"]:
        ag = reg.agents[t["agent_id"]]
        by_id[t["txn_id"]] = LedgerTxn(t["txn_id"], TxnKind.PAYMENT, datetime.fromisoformat(t["timestamp"]), t["amount"],
                                       (Posting(ag.wallet_account, -t["amount"]), Posting(f"merchant:{t['merchant_id']}", t["amount"])),
                                       t["agent_id"], t["owner_id"], t["merchant_id"])
    pool = [Alert(a["alert_id"], ReasonCode(a["rule"]), a["severity"], a["subject_type"], a["subject_id"], tuple(a["txn_ids"]),
                  datetime.fromisoformat(a["raised_at"]), a["explanation"]) for a in d["alerts"]]
    queue = {a["alert_id"] for a in d["alerts"] if a["in_queue"]}
    alert = next(a for a in pool if a.alert_id == d["alert_id"])
    return alert, by_id, reg, pool, queue


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        if PATH.exists():
            sys.exit(f"{PATH.name} already exists; it is frozen and must not be regenerated.")
        freeze()
