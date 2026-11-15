"""Idempotency keys: the primary defence against duplicate and replayed payments.

Keys are scoped per agent. The same key with the same payment returns the
stored decision (no second charge). The same key with a different payment
is rejected as a conflict.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import Decision


@dataclass(frozen=True)
class StoredResult:
    payment_hash: str
    decision: Decision


class IdempotencyStore:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], StoredResult] = {}

    def get(self, agent_id: str, key: str) -> StoredResult | None:
        return self._store.get((agent_id, key))

    def put(self, agent_id: str, key: str, payment_hash: str, decision: Decision) -> None:
        existing = self._store.get((agent_id, key))
        if existing is not None and existing.payment_hash != payment_hash:
            raise ValueError("idempotency key already bound to a different payment")
        self._store[(agent_id, key)] = StoredResult(payment_hash, decision)
