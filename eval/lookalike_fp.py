"""Look-alike false positives on real, legitimate company names.

Source: SEC company_tickers.json (public). Every entry is a real, distinct
registrant, so every look-alike flag between two different companies is a
false positive.

Test A: real names checked against the suite world's trusted merchants.
Test B: the first N SEC entries (the largest registrants) act as the trusted
merchant list; every other distinct company is checked against them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentguard.lookalike import find_lookalike, levenshtein, skeleton
from agentguard.models import Merchant

ROOT = Path(__file__).resolve().parents[1]


def load_sec(path: Path) -> list[tuple[str, str]]:
    raw = json.loads(path.read_text())
    seen, out = set(), []
    for _, row in sorted(raw.items(), key=lambda kv: int(kv[0])):  # keys are the SEC's own ordering
        cik = str(row["cik_str"])
        if cik in seen:
            continue  # one company can have several tickers
        seen.add(cik)
        out.append((cik, row["title"]))
    return out


def flag_all(candidates, trusted, max_distance=2):
    tsk = [(t, {skeleton(t.name), skeleton(t.name, strip_filler=False)}) for t in trusted]
    hits = []
    for c in candidates:
        mine = {skeleton(c.name), skeleton(c.name, strip_filler=False)}
        # Cheap prefilter: same rules as find_lookalike, so only plausible pairs get the full check.
        plausible = [t for t, ts in tsk if any(abs(len(a) - len(b)) <= max_distance or (len(b) >= 6 and b in a)
                                               for a in mine for b in ts)]
        if plausible:
            m = find_lookalike(c, plausible, max_distance)
            if m:
                hits.append(m)
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sec", default=str(ROOT / "data" / "sec" / "company_tickers.json"))
    ap.add_argument("--trusted", type=int, default=500)
    args = ap.parse_args()
    sec = load_sec(Path(args.sec))
    companies = [Merchant(f"sec-{cik}", name, "company", trusted=False) for cik, name in sec]

    world = json.loads((ROOT / "redteam" / "suite" / "world-v1.json").read_text())
    world_trusted = [Merchant(m["id"], m["name"], m["category"], trusted=True) for m in world["merchants"]]
    a = flag_all(companies, world_trusted)

    trusted = [Merchant(m.merchant_id, m.name, "company", trusted=True) for m in companies[:args.trusted]]
    rest = companies[args.trusted:]
    b = flag_all(rest, trusted)
    contains = sum(1 for m in b if m.contains_brand)
    out = {
        "source": "SEC company_tickers.json (public)", "distinct_companies": len(companies),
        "test_a_vs_world_merchants": {"checked": len(companies), "flagged": len(a),
                                      "pct": round(100 * len(a) / len(companies), 3),
                                      "examples": [[m.merchant_name, m.resembles_name, m.distance] for m in a[:20]]},
        "test_b_vs_top_registrants": {"trusted_list_size": len(trusted), "checked": len(rest), "flagged": len(b),
                                      "pct": round(100 * len(b) / len(rest), 2),
                                      "by_reason": {"contains_trusted_name": contains, "edit_distance_only": len(b) - contains},
                                      "examples": [[m.merchant_name, m.resembles_name, m.distance, m.contains_brand] for m in b[:40]]},
    }
    p = ROOT / "eval" / "results" / "lookalike_fp.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "examples"})
                      for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
