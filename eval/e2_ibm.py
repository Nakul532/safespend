"""E2: AgentGuard's AML rules on the IBM AML synthetic public benchmark (HI-Small).

Data: IBM "Transactions for Anti Money Laundering", CDLA-Sharing-1.0. Not
redistributed; place files in data/ibm-aml/. Results are labelled
"synthetic public benchmark".

The rules were written for AI agents paying merchants. They run here
unchanged, with bank-scale settings chosen BEFORE looking at the labels
(from ComplianceGuard's original thresholds). No tuning against labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agentguard.aml import rules
from agentguard.aml.rules import AmlConfig
from agentguard.models import Merchant
from agentguard.money import usd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ibm-aml"

# ASSUMPTION: approximate September 2022 rates to US dollars, used only to put amounts on one scale.
FX = {"US Dollar": 1.0, "Euro": 1.0, "UK Pound": 1.16, "Swiss Franc": 1.03, "Yuan": 0.145, "Yen": 0.0071,
      "Rupee": 0.0125, "Ruble": 0.0165, "Canadian Dollar": 0.76, "Australian Dollar": 0.68, "Mexican Peso": 0.05,
      "Brazil Real": 0.19, "Shekel": 0.29, "Saudi Riyal": 0.266, "Bitcoin": 20000.0}

# Bank-scale settings fixed before reading labels (ComplianceGuard: CTR structuring band $9,000-$9,999,
# rapid-fire 5+ in an hour; round wires in $1,000 units).
BANK_CFG = replace(AmlConfig(), structuring_band_low=0.9, structuring_min_count=3, structuring_window_hours=24 * 7,
                   rapid_fire_window_seconds=3600, rapid_fire_min_count=5, round_unit=usd(1000), round_min_count=3,
                   fan_in_min_agents=5)
CTR_THRESHOLD = usd(10_000)
BANK_RULES = (rules.structuring, rules.velocity_spike, rules.rapid_fire, rules.round_amounts,
              rules.dormant_then_active, rules.fan_in)


class Txn:
    __slots__ = ("txn_id", "timestamp", "amount", "agent_id", "merchant_id", "owner_id", "label", "key")

    def __init__(self, i, ts, amount, src, dst, label, key):
        self.txn_id, self.timestamp, self.amount = i, ts, amount
        self.agent_id, self.merchant_id, self.owner_id = src, dst, src
        self.label, self.key = label, key


class _Agents(dict):
    @dataclass(frozen=True)
    class _A:
        approval_threshold: int = CTR_THRESHOLD

    def __missing__(self, k):
        return self._A()

    def get(self, k, default=None):
        return self._A()


class _Merchants(dict):
    def get(self, k, default=None):
        return Merchant(k, k, "bank_account", trusted=False)


class BankRegistry:
    """Shim so the agent rules run on bank accounts: every account is an 'agent' with a $10,000
    reporting threshold, and every receiver is an untrusted 'merchant'."""
    agents = _Agents()
    merchants = _Merchants()

    def trusted_merchants(self):
        return []


def load(days: int | None):
    path = DATA / "HI-Small_Trans.csv"
    txns = []
    start = None
    with path.open(newline="") as f:
        r = csv.reader(f)
        next(r)
        for i, row in enumerate(r):
            ts = datetime.strptime(row[0], "%Y/%m/%d %H:%M").replace(tzinfo=timezone.utc)
            start = start or ts.replace(hour=0, minute=0)
            if days is not None and ts >= start + timedelta(days=days):
                continue
            amt = round(float(row[7]) * FX.get(row[8], 1.0), 6)
            txns.append(Txn(f"I{i}", ts, int(amt * 1_000_000), f"{row[1]}:{row[2]}", f"{row[3]}:{row[4]}",
                            row[10] == "1", tuple(row[:8]) if row[10] == "1" else None))
    txns.sort(key=lambda t: (t.timestamp, t.txn_id))
    return txns


def load_patterns():
    pat = {}
    name = None
    for line in (DATA / "HI-Small_Patterns.txt").read_text().splitlines():
        if line.startswith("BEGIN LAUNDERING ATTEMPT"):
            name = line.split("-", 1)[1].split(":")[0].strip()
        elif line.startswith("END"):
            name = None
        elif name and line.strip():
            pat[tuple(line.split(",")[:8])] = name
    return pat


def prf(flagged: set, labels: dict, negatives: int):
    tp = sum(1 for t in flagged if labels[t])
    pos = sum(labels.values())
    return {"flagged": len(flagged), "tp": tp, "precision": round(tp / len(flagged), 4) if flagged else None,
            "recall": round(tp / pos, 4) if pos else None, "fpr": round((len(flagged) - tp) / negatives, 6)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None, help="limit to the first N days (default: all)")
    ap.add_argument("--out", default=str(ROOT / "eval" / "results" / "e2_ibm.json"))
    args = ap.parse_args()
    t0 = time.time()
    txns = load(args.days)
    labels = {t.txn_id: t.label for t in txns}
    by_id = {t.txn_id: t for t in txns}
    patterns = load_patterns()
    tpat = {t.txn_id: patterns.get(t.key) for t in txns if t.label}
    neg = sum(1 for t in txns if not t.label)
    pos = len(txns) - neg
    print(f"loaded {len(txns):,} txns ({pos:,} laundering) in {time.time() - t0:.0f}s", flush=True)

    reg = BankRegistry()
    alerts = []
    per_rule = {}
    for rule in BANK_RULES:
        t1 = time.time()
        a = rule(txns, reg, BANK_CFG)
        alerts += a
        per_rule[rule.__name__] = {"alerts": len(a), "seconds": round(time.time() - t1, 1),
                                   **prf({x for al in a for x in al.txn_ids}, labels, neg),
                                   "alert_to_case": round(sum(1 for al in a if any(labels[x] for x in al.txn_ids)) / len(a), 4) if a else None}
        print(f"  {rule.__name__}: {len(a):,} alerts in {time.time() - t1:.0f}s", flush=True)

    all_flag = {x for al in alerts for x in al.txn_ids}
    base_flag = {t.txn_id for t in txns if t.amount >= CTR_THRESHOLD}
    result = {
        "benchmark": "IBM AML HI-Small (synthetic public benchmark, CDLA-Sharing-1.0)",
        "subset": "all days" if args.days is None else f"first {args.days} days",
        "transactions": len(txns), "laundering": pos,
        "fx_note": "ASSUMPTION: fixed approximate 2022 FX rates to USD",
        "settings_note": "Bank-scale rule settings fixed before reading labels; no tuning against labels",
        "unbudgeted": {"all_rules": {**prf(all_flag, labels, neg), "alerts": len(alerts),
                                     "alert_to_case": round(sum(1 for al in alerts if any(labels[x] for x in al.txn_ids)) / len(alerts), 4) if alerts else None},
                       "baseline_amount_>=_10000": prf(base_flag, labels, neg),
                       "per_rule": per_rule},
    }

    # Recall per laundering pattern.
    pat_tot = Counter(v or "unlabelled pattern" for v in tpat.values())
    pat_rules = Counter((tpat[x] or "unlabelled pattern") for x in all_flag if labels[x])
    pat_base = Counter((tpat[x] or "unlabelled pattern") for x in base_flag if labels[x])
    result["recall_by_pattern"] = {p: {"laundering_txns": n, "rules_recall": round(pat_rules[p] / n, 4),
                                       "baseline_recall": round(pat_base[p] / n, 4)} for p, n in pat_tot.most_common()}

    # Daily alert budgets: rules ranked by severity then total amount; baseline ranks single transactions by amount.
    def day(dt):
        return dt.date().isoformat()
    rule_by_day = defaultdict(list)
    for al in alerts:
        rule_by_day[day(al.raised_at)].append(al)
    txn_by_day = defaultdict(list)
    for t in txns:
        txn_by_day[day(t.timestamp)].append(t)
    budgets = {}
    for k in (10, 50, 100, 500):
        rf, bf, rcase, ralerts = set(), set(), 0, 0
        for d, als in rule_by_day.items():
            top = sorted(als, key=lambda a: (-a.severity, -sum(by_id[x].amount for x in a.txn_ids)))[:k]
            ralerts += len(top)
            rcase += sum(1 for a in top if any(labels[x] for x in a.txn_ids))
            rf |= {x for a in top for x in a.txn_ids}
        bcase = 0
        for d, ts in txn_by_day.items():
            top = sorted(ts, key=lambda t: -t.amount)[:k]
            bf |= {t.txn_id for t in top}
            bcase += sum(1 for t in top if t.label)
        budgets[f"K={k}/day"] = {
            "rules": {**prf(rf, labels, neg), "alerts_reviewed": ralerts,
                      "alert_precision": round(rcase / ralerts, 4) if ralerts else None},
            "baseline_top_amounts": {**prf(bf, labels, neg), "alerts_reviewed": len(bf),
                                     "alert_precision": round(bcase / len(bf), 4) if bf else None},
        }
    result["daily_alert_budgets"] = budgets
    result["days"] = len(txn_by_day)
    result["runtime_seconds"] = round(time.time() - t0)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("subset", "transactions", "laundering", "days", "runtime_seconds")}))


if __name__ == "__main__":
    main()
