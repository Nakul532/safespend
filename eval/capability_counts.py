"""Counts held-out scenarios that depend on capabilities the world doesn't model.

Classifies each scenario's missing_capabilities tags by keyword and prints
counts only (no tag text, no scenario content).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "recurring_charges": r"recurr|subscri|renew|repeat_charg|auto_?bill|billing_cycle|periodic",
    "stored_credentials": r"stored|saved_card|card_on_file|credential|vault|tokeni[sz]|payment_method|mandate",
    "future_liabilities": r"future|liabilit|deferred|commit|obligation|installment|prepay|accrual|contract_term",
}
OUT = {}
for name in ("heldout-model-v1", "heldout-external-v1", "heldout-owner-v1"):
    s = json.loads((ROOT / "redteam" / "heldout" / f"{name}.json").read_text())
    sc = s["scenarios"]
    row = {"scenarios": len(sc), "with_any_missing_capability": 0, "any_of_the_three": 0}
    for g in GROUPS:
        row[g] = 0
    other_tags = 0
    for x in sc:
        tags = [t.lower() for t in (x.get("missing_capabilities") or [])]
        if tags:
            row["with_any_missing_capability"] += 1
        hit_any = False
        for g, rx in GROUPS.items():
            if any(re.search(rx, t) for t in tags):
                row[g] += 1
                hit_any = True
        row["any_of_the_three"] += hit_any
        other_tags += sum(1 for t in tags if not any(re.search(rx, t) for rx in GROUPS.values()))
    row["tags_in_other_groups"] = other_tags
    OUT[name] = row
(ROOT / "eval" / "results").mkdir(parents=True, exist_ok=True)
(ROOT / "eval" / "results" / "capability_counts.json").write_text(json.dumps(OUT, indent=2))
for k, v in OUT.items():
    print(k, v)
