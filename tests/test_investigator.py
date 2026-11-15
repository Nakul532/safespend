"""Investigator v4: code builds the evidence pack; the model's lines are checked before display. LLM mocked."""
import json
from datetime import timedelta

from safespend.evidence import build
from safespend.investigator import Investigator, identifiers_for, verify
from safespend.llm import MockLlmClient
from safespend.synth import generate
from eval.e3.reference import load


def ref():
    a, by_id, reg, pool, queue = load()
    pack = build(a, by_id, reg, pool=pool, queue=queue)
    return a, by_id, reg, pack


def kinds(pack):
    return {f.kind: f.id for f in pack.facts}


def test_reference_pack_has_the_evidence_hand_review_asked_for():
    a, _, _, pack = ref()
    txt = "\n".join(f.text for f in pack.facts)
    assert "agent_08 (team ops): 6 payments" in txt and "87.0%–98.5% of its $500.00 approval threshold" in txt
    assert "within 28 h 15 m" in txt  # 10 payments in about 28 hours
    assert "Orbit Tools (software, untrusted)" in txt and "Nimbus Resell (compute, untrusted)" in txt
    assert "switched from Orbit Tools to Nimbus Resell" in txt
    assert "A83303da58c (structuring" in txt  # cross-alert link
    assert [f.id for f in pack.facts] == [f"E{i}" for i in range(1, len(pack.facts) + 1)]


def test_claim_checks_and_template():
    a, by_id, reg, pack = ref()
    k = kinds(pack)
    agent08 = next(f.id for f in pack.facts if f.text.startswith("agent_08"))
    data = {"recommendation": "escalate",
            "summary": [{"text": "Several ops agents kept payments just under their thresholds.", "cites": [agent08, "E3"]},
                        {"text": "This could be routine procurement.", "cites": ["E1"]},
                        {"text": "The payments came in a rapid burst.", "cites": [k["span"]]},
                        {"text": "All payments fell within a short period.", "cites": [k["span"]]},
                        {"text": "It may be structuring.", "cites": ["E1"]},
                        {"text": "The total was $3,844.", "cites": ["E2"]},
                        {"text": "Ten payments in all.", "cites": ["E2"]},
                        {"text": "Unsupported claim.", "cites": []},
                        {"text": "Cites a ghost.", "cites": ["E99"]}],
            "evidence": [{"cite": k["switch"], "why": "the agent moved to a second untrusted merchant"}],
            "open_questions": [{"text": "Is there a purchase order for these services?", "cites": []},
                               {"text": "Check whether there is a contract.", "cites": []}],
            "actions": [{"text": "Hold agent_08 pending review.", "cites": [agent08]}],
            "reason": {"text": "Team-wide payments sit just under approval thresholds at untrusted merchants.", "cites": ["E3", agent08]}}
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    s = n.sections
    assert [x["text"][:7] for x in s["summary"]] == ["Several"]
    assert s["evidence"][0]["facts"][0].startswith("agent_08 switched")  # code inserts the figures
    assert len(s["open_questions"]) == 1 and len(s["actions"]) == 1 and len(s["reason"]) == 1
    assert n.dropped == {"argues against the alert's computed facts": 1, "claims a burst without support": 1,
                         "claims a short period without support": 1, "states a doubt outside open questions": 1,
                         "contains a number": 1, "contains a spelled-out number": 1, "no citation": 1,
                         "cites an ID not in the pack": 1, "open question not phrased as a question": 1}


def test_just_under_needs_eighty_percent_for_every_cited_payment():
    sh = generate(301)
    a = next(x for x in sh.alerts if str(x.rule) == "AML_LOOKALIKE_MERCHANT")
    pack = build(a, sh.by_id, sh.registry, pool=sh.pool)
    low = [f.id for f in pack.facts if f.kind == "agent" and f.data["min_pct"] < 80]
    if low:
        n = verify(a.alert_id, {"summary": [{"text": "Each payment stayed just under the threshold.", "cites": low}]},
                   pack, sh.by_id, identifiers_for(pack, sh.registry))
        assert n.dropped == {"claims 'just under the threshold' without support": 1}


def test_burst_allowed_when_the_pack_shows_one():
    sh = generate(301)
    for a in sh.alerts:
        pack = build(a, sh.by_id, sh.registry, pool=sh.pool)
        b = next((f for f in pack.facts if f.kind == "burst" and f.data["span_s"] <= 600), None)
        if b:
            n = verify(a.alert_id, {"summary": [{"text": "The agent paid in a rapid burst.", "cites": [b.id]}]},
                       pack, sh.by_id, identifiers_for(pack, sh.registry))
            assert len(n.sections["summary"]) == 1
            return
    raise AssertionError("no burst in seed 301")


def test_draft_with_mock_model_and_failure():
    sh = generate(3)
    a = sh.alerts[0]
    reply = json.dumps({"recommendation": "more_info", "summary": [{"text": "See the rule.", "cites": ["E1"]}],
                        "reason": {"text": "The rule fired.", "cites": ["E1"]}})
    n = Investigator(MockLlmClient(lambda m: reply)).draft(a, sh.by_id, sh.registry, pool=sh.pool)
    assert n.sections["summary"] and n.recommendation == "more_info" and n.pack_facts
    bad = Investigator(MockLlmClient(lambda m: "nope")).draft(a, sh.by_id, sh.registry)
    assert bad.error == "unparseable" and bad.kept_lines == 0


def test_agent_names_with_unicode_spaces_are_identifiers_not_numbers():
    a, by_id, reg, pack = ref()
    agent08 = next(f.id for f in pack.facts if f.text.startswith("agent_08"))
    data = {"evidence": [{"cite": agent08, "why": "Agent 08 made most payments near‑threshold"}],
            "summary": [{"text": "The payments fell within a short timeframe.", "cites": ["E6"]}]}  # E6: 28 h span
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    assert n.sections["evidence"][0]["text"] == "Agent 08 made most payments near-threshold"
    assert n.dropped == {"claims a short period without support": 1}
