"""Runs every AML rule over the ledger and tracks which alerts are new."""
from __future__ import annotations

from ..ledger import Ledger
from ..registry import Registry
from .rules import ALL_RULES, Alert, AmlConfig


class AmlMonitor:
    def __init__(self, registry: Registry, config: AmlConfig | None = None) -> None:
        self.registry = registry
        self.config = config or AmlConfig()
        self.alerts: dict[str, Alert] = {}  # alert_id -> latest version

    def scan_ledger(self, ledger: Ledger) -> list[Alert]:
        """Scan all settled payments. Returns alerts not seen before; updates grown ones."""
        return self.scan(ledger.payments())

    def scan(self, payments: list) -> list[Alert]:
        txns = sorted(payments, key=lambda t: (t.timestamp, t.txn_id))
        new: list[Alert] = []
        for rule in ALL_RULES:
            for alert in rule(txns, self.registry, self.config):
                if alert.alert_id not in self.alerts:
                    new.append(alert)
                self.alerts[alert.alert_id] = alert
        return sorted(new, key=lambda a: (a.raised_at, a.alert_id))
