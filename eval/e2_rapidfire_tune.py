"""E2 round 2: retune the rapid-fire rule on IBM HI-Small days 1-3, test on days 4-7. ADDED AFTER STAGE 3 RESULTS.

Protocol, fixed before running:
- Tuning data: days 1-3 only. Day 4-7 labels are not touched until the setting is chosen.
- Grid: window in {60 s, 5 min, 15 min, 1 h, 6 h} x minimum count in {5, 10, 20, 40, 80}.
- Objective: transaction-level F1 of the rapid-fire rule alone on days 1-3; ties go to fewer alerts.
- Test: all six rules on days 4-7, once with the Stage 3 rapid-fire setting and once with the tuned one,
  next to the $10,000 baseline. Days 4-7 are run on their own (no warm-up from days 1-3).
Caveat: the Stage 3 report already showed 7-day aggregates, which include days 4-7.
"""
from __future__ import annotations

import json
import time
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from safespend.aml import rules
from eval.e2_ibm import BANK_CFG, BankRegistry, ROOT, evaluate, load, prf

WINDOWS = (60, 300, 900, 3600, 21600)
COUNTS = (5, 10, 20, 40, 80)


def f1(p, r):
    return 0.0 if not p or not r else round(2 * p * r / (p + r), 4)


def main() -> None:
    t0 = time.time()
    txns = load(7)
    cut = txns[0].timestamp.replace(hour=0, minute=0) + timedelta(days=3)
    train = [t for t in txns if t.timestamp < cut]
    test = [t for t in txns if t.timestamp >= cut]
    del txns
    print(f"train {len(train):,}  test {len(test):,}  ({time.time() - t0:.0f}s)", flush=True)

    labels = {t.txn_id: t.label for t in train}
    neg = sum(1 for t in train if not t.label)
    reg = BankRegistry()
    grid = []
    for w in WINDOWS:
        for k in COUNTS:
            cfg = replace(BANK_CFG, rapid_fire_window_seconds=w, rapid_fire_min_count=k)
            a = rules.rapid_fire(train, reg, cfg)
            m = prf({x for al in a for x in al.txn_ids}, labels, neg)
            row = {"window_s": w, "min_count": k, "alerts": len(a), **m, "f1": f1(m["precision"], m["recall"])}
            grid.append(row)
            print(row, flush=True)
    best = max(grid, key=lambda r: (r["f1"], -r["alerts"]))
    print("chosen", best, flush=True)
    del labels

    tuned = replace(BANK_CFG, rapid_fire_window_seconds=best["window_s"], rapid_fire_min_count=best["min_count"])
    before = evaluate(test, BANK_CFG)
    after = evaluate(test, BANK_CFG, {"rapid_fire": tuned})
    out = {
        "protocol": __doc__.strip(),
        "train": {"days": "1-3", "transactions": len(train), "laundering": sum(t.label for t in train)},
        "test": {"days": "4-7", "transactions": len(test), "laundering": sum(t.label for t in test)},
        "stage3_setting": {"window_s": BANK_CFG.rapid_fire_window_seconds, "min_count": BANK_CFG.rapid_fire_min_count},
        "grid_on_train": grid, "chosen": best,
        "test_before": before, "test_after": after, "runtime_seconds": round(time.time() - t0),
    }
    (ROOT / "eval" / "results" / "e2_rapidfire.json").write_text(json.dumps(out, indent=2))
    print("done", out["runtime_seconds"], "s")


if __name__ == "__main__":
    main()
