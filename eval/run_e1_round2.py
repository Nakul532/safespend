"""E1 round 2: the pre-payment split check and look-alike review hold, ADDED AFTER STAGE 3 RESULTS.

Frozen at tag eval-freeze-2 before any held-out set was run with them. Each held-out set runs once per
new config; only aggregates are saved. The v1 suite is reported too, but v1 is NOT a clean test here:
the builder saw the v1 structuring failures that motivated the split check.

The injection check reuses the run1 LLM cache (temperature 0; the three Stage 3 runs were identical),
so unchanged contexts get the same LLM answer; new contexts are sent live.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "redteam" / "runner"))
import redteam as rt  # noqa: E402

from eval.safespend_adapter import SafeSpendAdapter, Config, Stats  # noqa: E402
from eval.common import make_checker  # noqa: E402
from eval.run_e1 import SETS  # noqa: E402

BASE = dict(price_check=True, fuzzy_sanctions=True)
FULL = dict(injection=True, aml_monitoring=True, aml_hold_severity=7, run_tag="run1", **BASE)
CONFIGS = [
    Config("C1+S policy + price + fuzzy + split check", split_check=True, lookalike_hold_min_trusted=50, **BASE),
    Config("C4 full + split check", split_check=True, lookalike_hold_min_trusted=50, **FULL),
]
# Stage 4: the boss level's configuration. C4 plus the commitment holds; the intent check is inert on the
# suites (their steps carry no original request) and is evaluated on its own locked set.
C5 = Config("C5 boss: C4 + commitment holds", split_check=True, lookalike_hold_min_trusted=50, commitment_check=True, **FULL)


def main(configs=None, out_name="round2.json") -> None:
    out = ROOT / "eval" / "results" / "e1"
    loaded = {k: rt.load(p) for k, (_, p, _) in SETS.items()}
    for k, (s, w) in loaded.items():
        assert not rt.validate(s, w), k
        assert rt.check_lock(SETS[k][1]) is None or k != "v1"
    checker = make_checker("run1")
    res: dict = {"sets": {k: v[0] for k, v in SETS.items()}, "results": {}}
    for cfg in configs or CONFIGS:
        for k, (s, w) in loaded.items():
            r = rt.run_suite(SafeSpendAdapter(cfg, checker=checker, stats=Stats()), s, w)
            agg = {x: r[x] for x in ("overall", "adaptive_attacks", "by_category")}
            agg["after_lock"] = cfg.after_lock
            res["results"].setdefault(k, {})[cfg.name] = agg
            if not SETS[k][2]:
                (out / f"v1__{cfg.name.split()[0]}.json").write_text(json.dumps(r, indent=2, default=str))
        print(cfg.name, "LLM live calls", checker.calls, "cache hits", checker.cache_hits, flush=True)
    (out / out_name).write_text(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    import sys as _s
    main([C5], "c5_boss.json") if "--c5" in _s.argv else main()
