"""Double-entry mock settlement ledger. SIMULATED money only.

Every journal entry is a set of postings whose amounts sum to zero.
A payment moves money from an agent wallet to a merchant account and is
only accepted with a SettlementPermit signed by the PolicyEngine.
"""
from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .clock import Clock
from .models import Agent, PaymentRequest, SettlementPermit
from .signing import Signer

EXTERNAL_FUNDING = "external:funding"


class LedgerError(Exception):
    pass


@dataclass(frozen=True)
class Posting:
    account: str
    amount: int  # signed micro-dollars; the postings of one entry sum to zero


class TxnKind(StrEnum):
    PAYMENT = "payment"
    FUNDING = "funding"


@dataclass(frozen=True)
class LedgerTxn:
    txn_id: str
    kind: TxnKind
    timestamp: datetime
    amount: int
    postings: tuple[Posting, ...]
    agent_id: str
    owner_id: str
    merchant_id: str | None = None
    decision_id: str | None = None
    payment_hash: str | None = None
    idempotency_key: str | None = None
    invoice_ref: str | None = None


def merchant_account(merchant_id: str) -> str:
    return f"merchant:{merchant_id}"


class Ledger:
    def __init__(self, clock: Clock, permit_signer: Signer) -> None:
        self._clock = clock
        self._signer = permit_signer
        self._txns: list[LedgerTxn] = []
        self._balances: dict[str, int] = defaultdict(int)
        self._used_permits: set[str] = set()
        self._seq = itertools.count(1)

    # -- writes -------------------------------------------------------------

    def _post(self, txn: LedgerTxn) -> LedgerTxn:
        if sum(p.amount for p in txn.postings) != 0:
            raise LedgerError("unbalanced entry")
        for p in txn.postings:
            new_balance = self._balances[p.account] + p.amount
            if new_balance < 0 and not p.account.startswith("external:"):
                raise LedgerError(f"{p.account} would go negative")
        for p in txn.postings:
            self._balances[p.account] += p.amount
        self._txns.append(txn)
        return txn

    def fund(self, agent: Agent, amount: int, memo: str = "") -> LedgerTxn:
        """Load SIMULATED money into an agent wallet from the external funding account."""
        if amount <= 0:
            raise LedgerError("funding amount must be positive")
        txn = LedgerTxn(
            txn_id=f"F{next(self._seq):07d}",
            kind=TxnKind.FUNDING,
            timestamp=self._clock.now(),
            amount=amount,
            postings=(Posting(EXTERNAL_FUNDING, -amount), Posting(agent.wallet_account, amount)),
            agent_id=agent.agent_id,
            owner_id=agent.owner_id,
        )
        return self._post(txn)

    def settle(self, permit: SettlementPermit, request: PaymentRequest, agent: Agent) -> LedgerTxn:
        """Settle a payment. Refuses anything without a valid, unused permit for this exact payment."""
        if not self._signer.verify(permit.signed_fields(), permit.signature):
            raise LedgerError("permit signature invalid: payment did not pass validate_payment()")
        if permit.decision_id in self._used_permits:
            raise LedgerError("permit already used")
        if (
            permit.payment_hash != request.payment_hash
            or permit.amount != request.amount
            or permit.merchant_id != request.merchant_id
            or permit.agent_id != request.agent_id
            or agent.agent_id != request.agent_id
        ):
            raise LedgerError("permit does not match this payment")
        txn = LedgerTxn(
            txn_id=f"T{next(self._seq):07d}",
            kind=TxnKind.PAYMENT,
            timestamp=self._clock.now(),
            amount=request.amount,
            postings=(
                Posting(agent.wallet_account, -request.amount),
                Posting(merchant_account(request.merchant_id), request.amount),
            ),
            agent_id=agent.agent_id,
            owner_id=agent.owner_id,
            merchant_id=request.merchant_id,
            decision_id=permit.decision_id,
            payment_hash=request.payment_hash,
            idempotency_key=request.idempotency_key,
            invoice_ref=request.invoice_ref,
        )
        self._post(txn)
        self._used_permits.add(permit.decision_id)
        return txn

    # -- reads --------------------------------------------------------------

    def balance(self, account: str) -> int:
        return self._balances.get(account, 0)

    def balances(self) -> dict[str, int]:
        return dict(self._balances)

    def trial_balance(self) -> int:
        """Sum of every account. Always zero in a correct double-entry ledger."""
        return sum(self._balances.values())

    def transactions(self) -> list[LedgerTxn]:
        return list(self._txns)

    def get(self, txn_id: str) -> LedgerTxn | None:
        for t in self._txns:
            if t.txn_id == txn_id:
                return t
        return None

    def payments(self, since: datetime | None = None) -> list[LedgerTxn]:
        return [
            t for t in self._txns
            if t.kind is TxnKind.PAYMENT and (since is None or t.timestamp >= since)
        ]

    def recompute_balances(self) -> dict[str, int]:
        """Rebuild balances from postings alone (used to prove reconciliation)."""
        out: dict[str, int] = defaultdict(int)
        for t in self._txns:
            for p in t.postings:
                out[p.account] += p.amount
        return dict(out)
