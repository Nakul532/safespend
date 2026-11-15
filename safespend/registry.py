"""Who exists: agents, merchants and the humans allowed to approve."""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Agent, Merchant


@dataclass
class Registry:
    agents: dict[str, Agent] = field(default_factory=dict)
    merchants: dict[str, Merchant] = field(default_factory=dict)
    approvers: set[str] = field(default_factory=set)  # human user ids

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_id] = agent

    def add_merchant(self, merchant: Merchant) -> None:
        self.merchants[merchant.merchant_id] = merchant

    def agents_of_owner(self, owner_id: str) -> list[Agent]:
        return [a for a in self.agents.values() if a.owner_id == owner_id]

    def trusted_merchants(self) -> list[Merchant]:
        return [m for m in self.merchants.values() if m.trusted]
