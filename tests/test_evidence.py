"""Evidence pack and synthetic-data invariants (synth-v2)."""
import re

from safespend.evidence import LARGEST, MAX_ROWS, build
from safespend.money import fmt_usd
from safespend.synth import generate

SEEDS = (301, 302, 303, 20261114)
TOTAL = re.compile(r"(?:totalling|payments,) (\$[\d,]+\.\d\d)")


def test_alert_totals_equal_sum_of_rows_and_ids_follow_time():
    for seed in SEEDS:
        sh = generate(seed)
        assert all(t.amount % 10_000 == 0 for t in sh.txns)  # whole cents
        by_time = sorted(sh.txns, key=lambda t: (t.timestamp, t.txn_id))
        assert [t.txn_id for t in by_time] == sorted(t.txn_id for t in sh.txns)
        for i in range(1, len(by_time)):
            assert by_time[i].timestamp >= by_time[i - 1].timestamp
        for a in sh.pool:
            m = TOTAL.search(a.explanation)
            if m:
                assert m.group(1) == fmt_usd(sum(sh.by_id[t].amount for t in a.txn_ids)), (seed, a.explanation)


def test_pack_figures_recompute_from_rows_and_largest_are_always_shown():
    for seed in SEEDS:
        sh = generate(seed)
        for a in sh.alerts:
            p = build(a, sh.by_id, sh.registry, pool=sh.pool)
            txns = [sh.by_id[t] for t in a.txn_ids]
            ov = next(f for f in p.facts if f.kind == "overview")
            assert fmt_usd(sum(t.amount for t in txns)) in ov.text and ov.data["payments"] == len(txns)
            for f in p.facts:
                if f.kind in ("agent", "merchant"):
                    assert fmt_usd(sum(sh.by_id[t].amount for t in f.txns)) in f.text
            top = sorted(txns, key=lambda t: (-t.amount, t.txn_id))[:LARGEST]
            shown = {t.txn_id for t in p.rows}
            assert {t.txn_id for t in top} <= shown and len(p.rows) == min(MAX_ROWS, len(txns))
            assert sum(f.kind == "agent" for f in p.facts) == len({t.agent_id for t in txns})


def test_large_alert_says_how_many_rows_are_shown():
    for seed in SEEDS:
        sh = generate(seed)
        big = [a for a in sh.alerts if len(a.txn_ids) > MAX_ROWS]
        for a in big:
            p = build(a, sh.by_id, sh.registry)
            assert f"{MAX_ROWS} of {len(a.txn_ids)} shown" in p.text(sh.registry)
