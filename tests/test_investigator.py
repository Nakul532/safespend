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
            "why_it_matters": [{"text": "Several ops agents kept payments just under their thresholds.", "cites": [agent08, "E3"]},
                               {"text": "This could be routine procurement.", "cites": ["E1"]},
                               {"text": "The payments came in a rapid burst.", "cites": [k["span"]]},
                               {"text": "It is possible structuring.", "cites": ["E1"]},
                               {"text": "The total was $3,844.", "cites": ["E2"]},
                               {"text": "Ten payments in all.", "cites": ["E2"]},
                               {"text": "Unsupported claim.", "cites": []},
                               {"text": "Cites a ghost.", "cites": ["E99"]}],
            "open_questions": [{"text": "Is there a purchase order for these services?", "cites": []},
                               {"text": "Check whether there is a contract.", "cites": []}],
            "actions": [{"text": "Hold agent_08 pending review.", "cites": [agent08]}],
            "summary": [{"text": "Model-written summaries are ignored.", "cites": ["E1"]}]}
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    s = n.sections
    assert [x["text"] for x in s["why"]] == ["Several ops agents kept payments just under their thresholds."]
    assert len(s["open_questions"]) == 1 and len(s["actions"]) == 1
    assert s["summary"] == [{**s["summary"][0], "by": "code"}] and s["summary"][0]["text"] == (
        "Team structuring: 10 payments totalling $3,844.39 from 3 agents to 2 merchants, over about 28 hours, "
        "at 84.9%–98.5% of the agents' approval thresholds; all to untrusted merchants.")
    assert s["reason"][0]["by"] == "code" and s["reason"][0]["text"].startswith("Team structuring rule, severity 8:")
    assert "Every payment is at 80% or more" in s["reason"][0]["text"]
    assert n.dropped == {"argues against the alert's computed facts": 1, "describes timing itself instead of using the pack's label": 1,
                         "states a doubt outside open questions": 1, "contains a number": 1, "contains a spelled-out number": 1,
                         "no citation": 1, "cites an ID not in the pack": 1, "open question not phrased as a question": 1}


def test_just_under_needs_eighty_percent_for_every_cited_payment():
    sh = generate(301)
    a = next(x for x in sh.alerts if str(x.rule) == "AML_LOOKALIKE_MERCHANT")
    pack = build(a, sh.by_id, sh.registry, pool=sh.pool)
    low = [f.id for f in pack.facts if f.kind == "agent" and f.data["min_pct"] < 80]
    if low:
        n = verify(a.alert_id, {"why_it_matters": [{"text": "Each payment stayed just under the threshold.", "cites": low}]},
                   pack, sh.by_id, identifiers_for(pack, sh.registry))
        assert n.dropped == {"claims 'just under the threshold' without support": 1}


def test_timing_labels_are_computed_by_code():
    from safespend.evidence import timing_label
    assert [timing_label(x) for x in (30, 300, 3000, 20 * 3600, 28.25 * 3600, 6 * 86400)] == [
        "within a minute", "within minutes", "within an hour", "within one day", "over about 28 hours", "over about 6 days"]
    a, _, _, pack = ref()
    span = next(f for f in pack.facts if f.kind == "span")
    assert 'Timing label: "over about 28 hours"' in span.text


def test_draft_with_mock_model_and_failure():
    sh = generate(3)
    a = sh.alerts[0]
    reply = json.dumps({"recommendation": "more_info", "why_it_matters": [{"text": "See the rule.", "cites": ["E1"]}]})
    n = Investigator(MockLlmClient(lambda m: reply)).draft(a, sh.by_id, sh.registry, pool=sh.pool)
    assert n.sections["why"] and n.sections["summary"] and n.sections["reason"] and n.recommendation == "more_info" and n.pack_facts
    bad = Investigator(MockLlmClient(lambda m: "nope")).draft(a, sh.by_id, sh.registry)
    assert bad.error == "unparseable" and bad.sections["summary"] and bad.sections["reason"] and not bad.sections["why"]


def test_agent_names_with_unicode_spaces_are_identifiers_not_numbers():
    a, by_id, reg, pack = ref()
    agent08 = next(f.id for f in pack.facts if f.text.startswith("agent_08"))
    data = {"why_it_matters": [{"text": "Agent\u202f08 made most payments near\u2011threshold", "cites": [agent08]},
                               {"text": "The payments fell within a short timeframe.", "cites": ["E6"]}]}  # timing in its own words
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    assert n.sections["why"][0]["text"] == "Agent 08 made most payments near-threshold"
    assert n.dropped == {"describes timing itself instead of using the pack's label": 1}


def test_filter_v22_questions_and_negated_excuses():
    a, by_id, reg, pack = ref()
    data = {"open_questions": [{"text": "Is there a legitimate business need for these payments?", "cites": ["E1"]}],
            "why_it_matters": [{"text": "Payments go to untrusted merchants without an evident legitimate purpose.", "cites": ["E7"]},
                        {"text": "This is routine procurement.", "cites": ["E1"]},
                        {"text": "There is nothing unusual here.", "cites": ["E1"]},
                        {"text": "These payments are not routine.", "cites": ["E1"]}]}
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    assert len(n.sections["open_questions"]) == 1
    assert [x["text"] for x in n.sections["why"]] == ["Payments go to untrusted merchants without an evident legitimate purpose.",
                                                      "These payments are not routine."]
    assert n.dropped == {"argues against the alert's computed facts": 2}
