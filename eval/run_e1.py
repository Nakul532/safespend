"""E1: run every locked set under every config. Writes eval/results/e1/.

Held-out sets: only aggregate results are saved (no per-scenario rows), so
they cannot be used to tune anything.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "redteam" / "runner"))
import redteam as rt  # noqa: E402

from eval.safespend_adapter import SafeSpendAdapter, Config, Stats  # noqa: E402
from eval.common import make_checker  # noqa: E402

SETS = {
    "v1": ("Suite v1 (110)", ROOT / "redteam/suite/agentguard-redteam-v1.json", False),
    "heldout-model": ("Held-out: model-written (18)", ROOT / "redteam/heldout/heldout-model-v1.json", True),
    "heldout-external": ("Held-out: external (6)", ROOT / "redteam/heldout/heldout-external-v1.json", True),
    "heldout-owner": ("Held-out: owner incidents (5)", ROOT / "redteam/heldout/heldout-owner-v1.json", True),
}
RUNS = ("run1", "run2", "run3")


def configs(run_tag: str) -> list[Config]:
    base = dict(price_check=True, fuzzy_sanctions=True)
    return [
        Config("C1 policy (as locked)"),
        Config("C1+ policy + price check + fuzzy sanctions", **base),
        Config("C2 policy + injection check", injection=True, run_tag=run_tag, **base),
        Config("C3- full, AML flags only", injection=True, aml_monitoring=True, run_tag=run_tag, **base),
        Config("C3 full, AML->hold sev 7", injection=True, aml_monitoring=True, aml_hold_severity=7, run_tag=run_tag, **base),
        Config("C3 sens, AML->hold sev 5", injection=True, aml_monitoring=True, aml_hold_severity=5, run_tag=run_tag, **base),
        Config("C3 sens, AML->hold sev 9", injection=True, aml_monitoring=True, aml_hold_severity=9, run_tag=run_tag, **base),
    ]


def main() -> None:
    out = ROOT / "eval" / "results" / "e1"
    out.mkdir(parents=True, exist_ok=True)
    loaded = {k: rt.load(p) for k, (_, p, _) in SETS.items()}
    for k, (s, w) in loaded.items():
        errs = rt.validate(s, w)
        assert not errs, f"{k} invalid: {len(errs)} errors"
        warn = rt.check_lock(SETS[k][1])
        assert warn is None or k != "v1", warn

    summary: dict = {"sets": {k: v[0] for k, v in SETS.items()}, "results": {}, "latency": {}}
    stats_by_cfg: dict[str, Stats] = {}
    t0 = time.time()
    # No-guardrails baseline.
    for k, (s, w) in loaded.items():
        r = rt.run_suite(rt.AllowAll(), s, w)
        summary["results"].setdefault(k, {})["C0 no guardrails"] = {"run1": {x: r[x] for x in ("overall", "adaptive_attacks", "by_category")}}
    for run_tag in RUNS:
        checker = make_checker(run_tag)
        for cfg in configs(run_tag):
            if not cfg.injection and run_tag != "run1":
                continue  # deterministic configs need one run
            stats = stats_by_cfg.setdefault(f"{cfg.name}|{run_tag}", Stats())
            for k, (s, w) in loaded.items():
                ad = SafeSpendAdapter(cfg, checker=checker, stats=stats)
                r = rt.run_suite(ad, s, w)
                agg = {x: r[x] for x in ("overall", "adaptive_attacks", "by_category")}
                agg["after_lock"] = cfg.after_lock
                summary["results"].setdefault(k, {}).setdefault(cfg.name, {})[run_tag] = agg
                if not SETS[k][2] and run_tag == "run1":
                    (out / f"{k}__{cfg.name.split()[0]}{'_' + cfg.name.split()[-1] if 'sens' in cfg.name else ''}.json").write_text(
                        json.dumps(r, indent=2, default=str))
            print(f"[{time.time() - t0:5.0f}s] {run_tag} {cfg.name}: LLM calls so far {checker.calls}, cache hits {checker.cache_hits}", flush=True)

    # Latency: deterministic configs (no LLM) and the first live LLM run.
    def pct(xs, p):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p / 100 * len(xs)))], 2) if xs else None

    det = [s.total_ms for s in stats_by_cfg["C1+ policy + price check + fuzzy sanctions|run1"].steps]
    llm_stats = stats_by_cfg["C2 policy + injection check|run1"].steps
    llm_steps = [s for s in llm_stats if s.llm_called]
    live = [s for s in llm_steps if not s.llm_cached]
    summary["latency"] = {
        "deterministic_path_ms": {"n": len(det), "p50": pct(det, 50), "p95": pct(det, 95), "max": pct(det, 100)},
        "llm_path_ms_end_to_end": {"n_live_calls": len(live), "p50": pct([s.total_ms for s in live], 50),
                                    "p95": pct([s.total_ms for s in live], 95)},
        "llm_api_ms": {"p50": pct([s.llm_ms for s in live if s.llm_ms], 50),
                       "p95": pct([s.llm_ms for s in live if s.llm_ms], 95)},
        "share_needing_llm": {"llm_steps": len(llm_steps), "all_steps": len(llm_stats),
                              "pct": round(100 * len(llm_steps) / len(llm_stats), 1)},
        "note": "Measured on this laptop. LLM-path figures use only live API calls in C2 run1; repeated identical "
                "contexts within a run were served from cache and are excluded from latency but counted as needing the LLM.",
        "cached_llm_steps_in_run1": sum(1 for s in llm_steps if s.llm_cached),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
