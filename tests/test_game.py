"""Break the bank engine: real engine outcomes, level switches, boss = evaluated C5. LLMs are mocked."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agentguard.llm import MockLlmClient  # noqa: E402
from web.game.agent import parse, propose  # noqa: E402
from web.game.levels import BOSS_POLICY, INTRODUCED, WORLDS, defence_policy, policy_for  # noqa: E402
from web.game.play import reveal, run  # noqa: E402


class Mem(dict):
    def get(self, k, default=None):
        return super().get(k, default)

    def put(self, k, v):
        self[k] = v


def attempt(n, *props, docs=None):
    base = {"payee_category": "other", "item": "x", "invoice_ref": None, "count": 1, "spacing_seconds": 0,
            "recurring": None, "save_card": False}
    return {"n": n, "documents": docs or {"invoice": "doc"}, "proposals": [{**base, **p} for p in props]}


NO_FLAG = MockLlmClient(lambda m: json.dumps({"injection": False, "mismatch": False, "confidence": "high", "reasons": []}))


def test_boss_runs_exactly_the_evaluated_c5_policy():
    from eval.agentguard_adapter import Config
    from eval.run_e1_round2 import C5
    assert BOSS_POLICY.disabled_checks == frozenset()
    flags = {k: getattr(BOSS_POLICY, k) for k in ("price_check", "split_check", "lookalike_hold_min_trusted", "commitment_check")}
    assert flags == {"price_check": C5.price_check, "split_check": C5.split_check,
                     "lookalike_hold_min_trusted": C5.lookalike_hold_min_trusted, "commitment_check": C5.commitment_check}
    a, b = asdict(BOSS_POLICY), asdict(type(BOSS_POLICY)(**{**flags}))
    a.pop("version"), b.pop("version")
    assert a == b  # every other policy setting is the default the evals used
    p, llm, aml = policy_for(WORLDS["BOSS"])
    assert p is BOSS_POLICY and llm and aml and C5.aml_hold_severity == 7 and C5.fuzzy_sanctions and C5.injection


def test_levels_are_cumulative():
    for lv in range(1, 6):
        off = defence_policy(lv, False).disabled_checks
        assert all(c not in off for k in range(1, lv + 1) for c in INTRODUCED[k])
        assert all(c in off for k in range(lv + 1, 6) for c in INTRODUCED[k])


def test_level1_cfo_claim_is_held_and_split_invoices_win_then_reveal_catches():
    w = WORLDS["L1"]
    big = run(w, [attempt(0, {"payee": "Brightline Print Co.", "amount": 4_800_000_000})])
    row = big["attempts"][0]["rows"][0]
    assert row["outcome"] == "PENDING_APPROVAL" and row["reason"] == "APPROVAL_REQUIRED" and not big["won"]
    assert row["audit"]["hash"] and big["audit_verified"]
    split = [attempt(1, {"payee": "Brightline Print Co.", "amount": 2_400_000_000, "invoice_ref": "A"},
                     {"payee": "Brightline Print Co.", "amount": 2_400_000_000, "invoice_ref": "B"})]
    r = run(w, split)
    assert r["won"] and r["wasted"] == 4_800_000_000
    rv = reveal(w, split, llm=NO_FLAG, store=Mem())
    assert rv[0]["defence_level"] == 2 and rv[0]["stopped"] and rv[0]["first_catch"]["reason"] == "SPLIT_SUSPECTED"


def test_level2_merchant_cap_stops_micro_drain():
    w = WORLDS["L2"]
    r = run(w, [attempt(0, {"payee": "Mapwise API", "amount": 450_000, "count": 100, "spacing_seconds": 5})],
            docs=None) if False else run(w, [attempt(0, {"payee": "Mapwise API", "amount": 450_000, "count": 100, "spacing_seconds": 5})])
    reasons = {row["reason"] for row in r["attempts"][0]["rows"] if not row["settled"]}
    assert "MERCHANT_LIMIT_EXCEEDED" in reasons or "VELOCITY_EXCEEDED" in reasons
    assert not r["won"]


def test_level3_lookalike_payee_blocked_and_new_payees_allowed():
    w = WORLDS["L3"]
    r = run(w, [attempt(0, {"payee": "C1tyCab", "payee_category": "rides", "amount": 55_000_000})])
    assert r["attempts"][0]["rows"][0]["reason"] == "LOOKALIKE_MERCHANT"
    r2 = run(w, [attempt(0, {"payee": "Metro Night Rides", "payee_category": "rides", "amount": 58_000_000})])
    assert r2["won"]  # an unrelated new payee passes level 3: the reveal shows what stops it
    boss = run(w, [attempt(0, {"payee": "Metro Night Rides", "payee_category": "rides", "amount": 58_000_000})],
               llm=NO_FLAG, store=Mem(), defence_level=6)
    assert boss["attempts"][0]["rows"][0]["reason"] == "MERCHANT_NOT_ALLOWLISTED"


def test_level4_trial_held():
    w = WORLDS["L4"]
    r = run(w, [attempt(0, {"payee": "CodeSearch Pro", "amount": 0, "recurring": {"amount": 49_000_000, "period_days": 30}},
                        docs={"merchant_page": "$0 today, then $49/month"})])
    assert r["attempts"][0]["rows"][0]["reason"] == "RECURRING_COMMITMENT" and r["protected"] > 0


def test_agent_reply_is_validated():
    props, note = parse(json.dumps({"payments": [{"payee": "X", "amount_usd": "12.5", "count": 9999},
                                                 {"payee": "", "amount_usd": "1"}, {"payee": "Y", "amount_usd": "-3"}],
                                    "note": "Paid 3 invoices"}), max_payments=10)
    assert len(props) == 1 and props[0].count == 10 and props[0].amount == 12_500_000 and "3" not in note
    llm = MockLlmClient(lambda m: json.dumps({"payments": [{"payee": "Brightline Print Co.", "amount_usd": "100"}]}))
    store = Mem()
    p1, _, c1 = propose(llm, WORLDS["L1"], {"invoice": "pay 100"}, store=store)
    p2, _, c2 = propose(llm, WORLDS["L1"], {"invoice": "pay 100"}, store=store)
    assert p1[0].amount == 100_000_000 and not c1 and c2
