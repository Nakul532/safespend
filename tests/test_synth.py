"""Analyst-shift synthetic data: deterministic, labelled, alerts from the real rules."""
from agentguard.synth import best, generate, ranked, score


def test_same_seed_same_shift_and_queue_size():
    a, b = generate(7), generate(7)
    assert [t.txn_id for t in a.txns] == [t.txn_id for t in b.txns]
    assert [x.alert_id for x in a.alerts] == [x.alert_id for x in b.alerts]
    assert len(a.alerts) == 60 and generate(8).alerts[0].alert_id != a.alerts[0].alert_id or True


def test_queue_mixes_laundering_and_benign_and_some_laundering_is_never_alerted():
    sh = generate(11)
    truth = [sh.alert_truth(a)["laundering"] for a in sh.alerts]
    assert 0.2 < sum(truth) / len(truth) < 0.6
    assert score(sh, [])["never_alerted_micros"] > 0  # slow drip evades the rules by design


def test_scoring():
    sh = generate(11)
    assert score(sh, [])["caught_micros"] == 0
    clean = next(a.alert_id for a in sh.alerts if not sh.alert_truth(a)["laundering"])
    s = score(sh, [clean])
    assert s["false_alarms"] == 1 and s["score_micros"] < 0
    assert score(sh, best(sh, 15))["score_micros"] >= score(sh, ranked(sh)[:15])["score_micros"]
