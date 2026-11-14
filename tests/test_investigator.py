"""Investigator case notes: code verifies citations and drops numbers. The LLM is mocked."""
import json

from agentguard.investigator import Investigator, verify
from agentguard.llm import MockLlmClient
from agentguard.synth import generate

ALLOWED = {"T0000001", "T0000002"}


def test_verify_keeps_cited_and_drops_bad_sentences():
    data = {"recommendation": "escalate", "sentences": [
        {"text": "Payments [T0000001] and [T0000002] sit just under agent_07's threshold.", "cites": ["T0000001", "T0000002"]},
        {"text": "The total was $480 [T0000001].", "cites": ["T0000001"]},
        {"text": "This looks like structuring.", "cites": []},
        {"text": "It matches [T0000099].", "cites": ["T0000099"]},
        {"text": "Four agents paid it [T0000001].", "cites": ["T0000001"]}]}
    n = verify("A1", data, ALLOWED, {"agent_07"})
    assert [s["cites"] for s in n.sentences] == [["T0000001", "T0000002"]]
    assert n.dropped == {"contains a number": 1, "no citation": 1, "cites an ID it was not shown": 1,
                         "contains a spelled-out number": 1}
    assert n.cited_unknown == 1 and n.recommendation == "escalate"


def test_draft_on_a_real_alert_with_mock_model():
    sh = generate(3)
    a = sh.alerts[0]
    tid = a.txn_ids[0]
    reply = json.dumps({"recommendation": "more_info", "sentences": [{"text": f"See [{tid}].", "cites": [tid]}]})
    n = Investigator(MockLlmClient(lambda m: reply)).draft(a, sh.by_id, sh.registry)
    assert n.sentences and n.recommendation == "more_info"
    bad = Investigator(MockLlmClient(lambda m: "nope")).draft(a, sh.by_id, sh.registry)
    assert bad.error == "unparseable" and not bad.sentences
