from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agentguard import AgentGuard, PaymentRequest, usd
from agentguard.clock import ManualClock
from agentguard.config import BreakerConfig, PolicyConfig
from agentguard.fixtures import OWNER_GROWTH, OWNER_MARKETS, RISK_OFFICER, demo_registry
from agentguard.ledger import LedgerTxn, Posting, TxnKind

START = datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc)

_keys = itertools.count(1)


def key() -> str:
    return f"idem-{next(_keys)}"


@pytest.fixture
def clock() -> ManualClock:
    return ManualClock(START)


def make_guard(clock: ManualClock, *, policy: PolicyConfig | None = None, breaker: BreakerConfig | None = None,
               registry=None, sanctions=None, fund: int = usd(100)) -> AgentGuard:
    g = AgentGuard(registry or demo_registry(), clock=clock, policy=policy,
                   breaker=breaker or BreakerConfig(spend_limit=usd(10_000), alert_limit=1_000), sanctions=sanctions)
    if fund > 0:
        for agent_id in g.registry.agents:
            g.fund(agent_id, fund)
    return g


@pytest.fixture
def guard(clock: ManualClock) -> AgentGuard:
    return make_guard(clock)


def req(agent: str = "agent_001", merchant: str = "m_newshub", amount: int = usd("0.002"), **kw) -> PaymentRequest:
    kw.setdefault("idempotency_key", key())
    return PaymentRequest(agent_id=agent, merchant_id=merchant, amount=amount, **kw)


def codes(decision) -> list[str]:
    return [f.code for f in decision.failed_checks]


# -- building ledger transactions directly, for AML rule tests ---------------

_txn_ids = itertools.count(1)


def txn(agent: str, merchant: str, amount: int, at: datetime, owner: str | None = None) -> LedgerTxn:
    owners = {"agent_001": OWNER_GROWTH, "agent_002": OWNER_MARKETS, "agent_003": OWNER_GROWTH}
    return LedgerTxn(
        txn_id=f"T{next(_txn_ids):07d}",
        kind=TxnKind.PAYMENT,
        timestamp=at,
        amount=amount,
        postings=(Posting(f"wallet:{agent}", -amount), Posting(f"merchant:{merchant}", amount)),
        agent_id=agent,
        owner_id=owner or owners.get(agent, "user_other"),
        merchant_id=merchant,
    )


__all__ = ["START", "OWNER_GROWTH", "OWNER_MARKETS", "RISK_OFFICER", "codes", "key", "make_guard", "replace",
           "req", "timedelta", "txn"]
