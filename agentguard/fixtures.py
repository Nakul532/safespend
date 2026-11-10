"""Demo agents and merchants, carried over from AgentPay. SIMULATED data only.

Prices and limits match AgentPay's originals. Owners are new: ResearchBot
and ContentBot share an owner so team-level limits and team structuring
have something to act on. All people are fictional placeholder ids.
"""
from __future__ import annotations

from .models import Agent, Merchant
from .money import usd
from .registry import Registry

MERCHANTS = (
    Merchant("m_weathercorp", "WeatherCorp", "data"),
    Merchant("m_newshub", "NewsHub", "data"),
    Merchant("m_finstream", "FinStream", "finance_data"),
    Merchant("m_oracleai", "OracleAI", "ai"),
    Merchant("m_moodsync", "MoodSync", "ai"),
    Merchant("m_computemesh", "ComputeMesh", "compute"),
    Merchant("m_pixelmint", "PixelMint", "ai"),
    Merchant("m_linguanet", "LinguaNet", "ai"),
    Merchant("m_codesandbox", "CodeSandbox", "compute"),
)

# AgentPay API price list (per call), in micro-dollars.
PRICES = {
    "m_weathercorp": usd("0.001"),
    "m_newshub": usd("0.002"),
    "m_finstream": usd("0.005"),
    "m_oracleai": usd("0.015"),
    "m_moodsync": usd("0.003"),
    "m_computemesh": usd("0.050"),
    "m_pixelmint": usd("0.020"),
    "m_linguanet": usd("0.001"),
    "m_codesandbox": usd("0.010"),
}

OWNER_GROWTH = "user_growth_lead"
OWNER_MARKETS = "user_markets_lead"
RISK_OFFICER = "user_risk_officer"

AGENTS = (
    Agent(
        agent_id="agent_001", name="ResearchBot-α", role="Market research agent", owner_id=OWNER_GROWTH,
        per_txn_limit=usd(5), daily_budget=usd(50), approval_threshold=usd(2),
        allowed_merchants=frozenset({"m_newshub", "m_finstream", "m_moodsync"}),
    ),
    Agent(
        agent_id="agent_002", name="TradingBot-β", role="Algorithmic trading agent", owner_id=OWNER_MARKETS,
        per_txn_limit=usd(10), daily_budget=usd(100), approval_threshold=usd(5),
        allowed_merchants=frozenset({"m_finstream", "m_oracleai", "m_computemesh"}),
    ),
    Agent(
        agent_id="agent_003", name="ContentBot-γ", role="Content generation agent", owner_id=OWNER_GROWTH,
        per_txn_limit=usd(3), daily_budget=usd(30), approval_threshold=usd(2),
        allowed_merchants=frozenset({"m_newshub", "m_pixelmint", "m_linguanet"}),
    ),
)


def demo_registry() -> Registry:
    reg = Registry()
    for m in MERCHANTS:
        reg.add_merchant(m)
    for a in AGENTS:
        reg.add_agent(a)
    # Every owner is also an approver, so four-eyes is tested for real:
    # each can approve the other team's payments but never their own.
    reg.approvers |= {OWNER_GROWTH, OWNER_MARKETS, RISK_OFFICER}
    return reg
