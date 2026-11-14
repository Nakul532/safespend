"""Intent check on the dev set (tuning) or the locked intent-v1 set (run once; aggregates only).
ADDED AFTER LOCK (Stage 4)."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from agentguard import Agent, AgentGuard, Merchant, Outcome, PaymentRequest, usd
from agentguard.clock import ManualClock
from agentguard.intent import Intent, IntentChecker
from agentguard.llm import GroqClient
from agentguard.registry import Registry
from eval.common import CACHE, MODEL, ROOT, load_env

SETS = {"dev": ROOT / "eval/dev/intent_dev.json", "locked": ROOT / "redteam/intent/intent-v1.json"}


def run_case(case, checker):
    clock = ManualClock(datetime(2026, 11, 16, 12, tzinfo=timezone.utc))
    p, it = case["proposal"], case["intent"]
    reg = Registry()
    reg.add_merchant(Merchant("m_case", p["merchant_name"], p["merchant_category"], trusted=False))
    reg.add_agent(Agent(agent_id="buyer", name="buyer", role="purchasing", owner_id="person", per_txn_limit=usd(100000),
                        daily_budget=usd(100000), approval_threshold=usd(100000), allowed_merchants=frozenset({"m_case"})))
    g = AgentGuard(reg, clock=clock, intent_checker=checker)
    g.fund("buyer", usd(200000))
    intent = Intent(it["request_text"], usd(Decimal(it["max_amount_usd"])) if it.get("max_amount_usd") else None,
                    frozenset(it["categories"]) if it.get("categories") else None, it.get("merchant_hint"))
    d = g.submit_payment(PaymentRequest("buyer", "m_case", usd(Decimal(p["amount_usd"])), "k-" + case["id"],
                                        description=p["item"], context=case.get("context") or {}, intent=intent))
    res = g.engine.last_intent
    return d.outcome is Outcome.PENDING_APPROVAL, res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("set", choices=SETS)
    ap.add_argument("--runs", type=int, default=1)
    args = ap.parse_args()
    load_env()
    cases = json.loads(SETS[args.set].read_text())["cases"]
    out = {"set": args.set, "cases": len(cases), "model": MODEL, "runs": {}}
    for r in range(1, args.runs + 1):
        checker = IntentChecker(GroqClient(default_model=MODEL), model=MODEL, cache_dir=CACHE / "intent",
                                run_tag=f"{args.set}-run{r}", min_interval_s=2.0)
        agg = Counter(); by = defaultdict(Counter); lat = []; rows = []
        for c in cases:
            held, res = run_case(c, checker)
            want = c["expected"] == "hold"
            k = "mismatch" if want else "match"
            agg[f"{k}_total"] += 1
            agg[f"{k}_{'held' if held else 'allowed'}"] += 1
            if want and held:
                agg["held_by_fields"] += bool(res.field_reasons)
                agg["held_by_model_only"] += not res.field_reasons
            if res.llm_error:
                agg["llm_errors"] += 1
            if res.llm_latency_ms:
                lat.append(res.llm_latency_ms)
            if args.set == "locked":
                by[f"difficulty:{c['difficulty']}"]["correct"] += held == want
                by[f"difficulty:{c['difficulty']}"]["total"] += 1
                if want:
                    by[f"type:{c['mismatch_type']}"]["held"] += held
                    by[f"type:{c['mismatch_type']}"]["total"] += 1
            else:  # dev set: per-case rows are fine to see
                rows.append({"id": c["id"], "expected": c["expected"], "held": held, "fields": list(res.field_reasons),
                             "llm": res.llm_mismatch, "conf": res.llm_confidence, "reasons": list(res.llm_reasons)})
        out["runs"][f"run{r}"] = {"totals": dict(agg), "breakdown": {k: dict(v) for k, v in by.items()},
                                  "llm_latency_ms_p50": round(statistics.median(lat)) if lat else None,
                                  "live_calls": checker.calls, "cache_hits": checker.cache_hits, **({"rows": rows} if rows else {})}
    dest = ROOT / "eval/results" / f"intent_{args.set}.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v["totals"] for k, v in out["runs"].items()}, indent=1))
    if rows:
        for x in rows:
            print(x)


if __name__ == "__main__":
    main()
