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
                        {"text": "The payments came {timing:E6}.", "cites": []},
                        {"text": "Timing from the wrong line {timing:E2}.", "cites": ["E2"]},
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
    assert [x["text"] for x in s["summary"]][:1] == ["Several ops agents kept payments just under their thresholds."]
    assert s["summary"][1]["text"] == "The payments came over about 28 hours." and s["summary"][1]["cites"] == ["E6"]
    assert s["evidence"][0]["facts"][0].startswith("agent_08 switched")  # code inserts the figures
    assert len(s["open_questions"]) == 1 and len(s["actions"]) == 1 and len(s["reason"]) == 1
    assert n.dropped == {"argues against the alert's computed facts": 1, "describes timing itself instead of using the pack's label": 2,
                         "timing label taken from a non-timing line": 1, "states a doubt outside open questions": 1,
                         "contains a number": 1, "contains a spelled-out number": 1, "no citation": 1,
                         "over the section limit": 1, "open question not phrased as a question": 1}


def test_just_under_needs_eighty_percent_for_every_cited_payment():
    sh = generate(301)
    a = next(x for x in sh.alerts if str(x.rule) == "AML_LOOKALIKE_MERCHANT")
    pack = build(a, sh.by_id, sh.registry, pool=sh.pool)
    low = [f.id for f in pack.facts if f.kind == "agent" and f.data["min_pct"] < 80]
    if low:
        n = verify(a.alert_id, {"summary": [{"text": "Each payment stayed just under the threshold.", "cites": low}]},
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
            "summary": [{"text": "The payments fell within a short timeframe.", "cites": ["E6"]}]}  # timing in its own words
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    assert n.sections["evidence"][0]["text"] == "Agent 08 made most payments near-threshold"
    assert n.dropped == {"describes timing itself instead of using the pack's label": 1}


def test_filter_v22_questions_and_negated_excuses():
    a, by_id, reg, pack = ref()
    data = {"open_questions": [{"text": "Is there a legitimate business need for these payments?", "cites": ["E1"]}],
            "reason": {"text": "Payments go to untrusted merchants without an evident legitimate purpose.", "cites": ["E7"]},
            "summary": [{"text": "This is routine procurement.", "cites": ["E1"]},
                        {"text": "There is nothing unusual here.", "cites": ["E1"]},
                        {"text": "These payments are not routine.", "cites": ["E1"]}]}
    n = verify(a.alert_id, data, pack, by_id, identifiers_for(pack, reg))
    assert len(n.sections["open_questions"]) == 1 and len(n.sections["reason"]) == 1
    assert [x["text"] for x in n.sections["summary"]] == ["These payments are not routine."]
    assert n.dropped == {"argues against the alert's computed facts": 2}
