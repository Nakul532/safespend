"""Checks on the red-team suite's structure and the runner's scoring.

These validate the suite file and test the runner on examples/mini-suite.json.
They never run any guardrail against the locked suite or the held-out sets.
"""
from __future__ import annotations

import collections
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

RT = Path(__file__).resolve().parents[1] / "redteam"
sys.path.insert(0, str(RT / "runner"))
import redteam as rt  # noqa: E402

SUITE = RT / "suite" / "agentguard-redteam-v1.json"
MINI = RT / "examples" / "mini-suite.json"


@pytest.fixture(scope="module")
def v1():
    return rt.load(SUITE)


def test_v1_is_valid(v1):
    assert rt.validate(*v1) == []


def test_v1_category_counts(v1):
    suite, _ = v1
    c = collections.Counter((s["kind"], s["category"]) for s in suite["scenarios"])
    expected = {"prompt_injection": 15, "structuring": 10, "lookalike_merchant": 8, "bait_and_switch": 7,
                "duplicate_replay": 5, "approval_bypass": 5, "sanctions": 5}
    for cat, n in expected.items():
        assert c[("attack", cat)] == n and c[("legitimate", cat)] == n, cat


def test_at_least_two_adaptive_attacks_per_category(v1):
    suite, _ = v1
    c = collections.Counter(s["category"] for s in suite["scenarios"] if s["adaptive"])
    assert all(c[cat] >= 2 for cat in rt.CATEGORIES), c


def test_every_step_has_a_realistic_amount(v1):
    suite, _ = v1
    for s in suite["scenarios"]:
        for step in s["steps"]:
            amt = Decimal(step["amount_usd"])
            assert Decimal("0.001") <= amt <= Decimal("1000"), (s["id"], amt)


def test_ids_follow_kind_and_category(v1):
    suite, _ = v1
    prefix = {"prompt_injection": "INJ", "structuring": "STR", "lookalike_merchant": "LKA", "bait_and_switch": "BAS",
              "duplicate_replay": "DUP", "approval_bypass": "APB", "sanctions": "SAN"}
    for s in suite["scenarios"]:
        assert s["id"].startswith(("ATK-" if s["kind"] == "attack" else "LEG-") + prefix[s["category"]])


def test_sanctions_near_misses_are_not_listed_names(v1):
    suite, world = v1
    listed = {n.casefold() for n in world["sanctions_list"]["entries"]}
    for s in suite["scenarios"]:
        if s["category"] == "sanctions" and s["kind"] == "legitimate":
            assert all(m["name"].casefold() not in listed for m in s["world_overrides"]["merchants_add"])


def test_lock_matches_files():
    assert rt.check_lock(SUITE) is None


def test_validator_catches_problems():
    suite, world = rt.load(MINI)
    bad = json.loads(json.dumps(suite))
    bad["scenarios"][0]["steps"][1]["offset_seconds"] = -5
    bad["scenarios"][1]["steps"][0]["malicious"] = True
    bad["scenarios"][0]["steps"][0]["merchant"] = "nowhere"
    errs = rt.validate(bad, world)
    assert any("never decreases" in e for e in errs)
    assert any("legitimate task cannot have malicious" in e for e in errs)
    assert any("unknown merchant" in e for e in errs)


def test_allow_all_scoring_on_mini_suite():
    suite, world = rt.load(MINI)
    r = rt.run_suite(rt.AllowAll(), suite, world)
    o = r["overall"]
    assert o["attacks_stopped"] == 0 and o["dollars_lost_usd"] == "3.90"  # both splits settled; loss allowed is 1.95
    assert o["false_blocks"] == 0 and o["double_charges"] == 1  # allow-all charges the retry again


def test_block_all_scoring_on_mini_suite():
    suite, world = rt.load(MINI)
    o = rt.run_suite(rt.BlockAll(), suite, world)["overall"]
    assert o["attacks_stopped"] == 1 and o["dollars_lost_usd"] == "0"
    assert o["false_blocks"] == 1


def test_adapter_contract_enforced():
    class Liar:
        name = "liar"
        def reset(self, *a): pass
        def submit(self, step, now): return {"decision": "block", "charged": True}
        def flags(self, now): return []
    suite, world = rt.load(MINI)
    with pytest.raises(ValueError, match="cannot also charge"):
        rt.run_suite(Liar(), suite, world)


def test_markdown_report_has_columns():
    suite, world = rt.load(MINI)
    md = rt.render_markdown({"none": rt.run_suite(rt.AllowAll(), suite, world),
                             "block": rt.run_suite(rt.BlockAll(), suite, world)})
    assert "| Metric | none | block |" in md and "SIMULATED" in md and "Adaptive attacks only" in md
