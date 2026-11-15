"""Tamper-evident audit log.

Each record stores the hash of the record before it. Editing, deleting or
reordering any record breaks the chain, and verify() reports where.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable

from .clock import Clock
from .models import canonical_json, sha256_hex

GENESIS_HASH = "0" * 64


class EventType(StrEnum):
    DECISION = "DECISION"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    SETTLED = "SETTLED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REFUSED = "APPROVAL_REFUSED"
    BREAKER_TRIPPED = "BREAKER_TRIPPED"
    BREAKER_RESUMED = "BREAKER_RESUMED"
    BREAKER_RESUME_REFUSED = "BREAKER_RESUME_REFUSED"
    AML_ALERT = "AML_ALERT"


@dataclass(frozen=True)
class AuditRecord:
    seq: int
    recorded_at: str  # ISO-8601 UTC
    event_type: str
    policy_version: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str

    def body(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "recorded_at": self.recorded_at,
            "event_type": self.event_type,
            "policy_version": self.policy_version,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    records_checked: int
    first_bad_seq: int | None = None
    problem: str | None = None


def verify_records(records: Iterable[AuditRecord]) -> VerifyResult:
    prev = GENESIS_HASH
    count = 0
    for expected_seq, rec in enumerate(records, start=1):
        count += 1
        if rec.seq != expected_seq:
            return VerifyResult(False, count, rec.seq, f"expected seq {expected_seq}, found {rec.seq}")
        if rec.prev_hash != prev:
            return VerifyResult(False, count, rec.seq, "prev_hash does not match the previous record")
        if sha256_hex(rec.body()) != rec.hash:
            return VerifyResult(False, count, rec.seq, "record contents do not match its hash")
        prev = rec.hash
    return VerifyResult(True, count)


class AuditLog:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._records: list[AuditRecord] = []

    def append(self, event_type: EventType, payload: dict[str, Any], policy_version: str) -> AuditRecord:
        # Round-trip through JSON so the stored payload is exactly what gets hashed and exported.
        clean = json.loads(canonical_json(payload))
        prev = self._records[-1].hash if self._records else GENESIS_HASH
        seq = len(self._records) + 1
        body = {
            "seq": seq,
            "recorded_at": self._clock.now().isoformat(),
            "event_type": str(event_type),
            "policy_version": policy_version,
            "payload": clean,
            "prev_hash": prev,
        }
        rec = AuditRecord(**body, hash=sha256_hex(body))
        self._records.append(rec)
        return rec

    def records(self) -> list[AuditRecord]:
        return list(self._records)

    def by_type(self, event_type: EventType) -> list[AuditRecord]:
        return [r for r in self._records if r.event_type == event_type]

    def verify(self) -> VerifyResult:
        return verify_records(self._records)

    def export_jsonl(self) -> str:
        """One JSON object per line, for auditors. Re-verify with load_jsonl()."""
        return "".join(canonical_json({**r.body(), "hash": r.hash}) + "\n" for r in self._records)

    @staticmethod
    def load_jsonl(text: str) -> list[AuditRecord]:
        return [AuditRecord(**json.loads(line)) for line in text.splitlines() if line.strip()]
