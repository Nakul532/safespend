"""Every AML rule has a positive test (fires) and a negative test (stays quiet)."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from agentguard import Merchant, ReasonCode as R, usd
from agentguard.aml import AmlConfig, AmlMonitor
from agentguard.aml import rules
from agentguard.audit import EventType
from agentguard.fixtures import demo_registry
from agentguard.lookalike import find_lookalike, skeleton
from conftest import START, make_guard, req, txn

CFG = AmlConfig()
H = timedelta(hours=1)
M = timedelta(minutes=1)
S = timedelta(seconds=1)
D = timedelta(days=1)


def reg():
    r = demo_registry()
    r.add_merchant(Merchant("m_fake_news", "N3wsHub", "data", trusted=False))
    r.add_merchant(Merchant("m_gift", "GiftBox Cards", "gift_cards", trusted=False))
    r.add_merchant(Merchant("m_newco", "Quillfeather Labs", "data", trusted=False))
    for i in range(5):
        r.add_merchant(Merchant(f"m_new{i}", f"Vendor{i} Analytics", "data", trusted=False))
    return r


def run(rule, txns, registry=None):
    return rule(sorted(txns, key=lambda t: t.timestamp), registry or reg(), CFG)


# agent_001: approval threshold $2, so the structuring band is $1.60-$1.99.

# -- structuring -------------------------------------------------------------------

def test_structuring_fires():
    ts = [txn("agent_001", "m_newshub", usd("1.95"), START + i * H) for i in range(3)]
    alerts = run(rules.structuring, ts)
    assert len(alerts) == 1 and alerts[0].rule is R.AML_STRUCTURING
    assert set(alerts[0].txn_ids) == {t.txn_id for t in ts}
    assert alerts[0].facts["total_micros"] == usd("5.85")


def test_structuring_quiet_when_spread_out_or_not_near_threshold():
    spread = [txn("agent_001", "m_newshub", usd("1.95"), START + i * 30 * H) for i in range(3)]
    small = [txn("agent_001", "m_newshub", usd("0.50"), START + i * H) for i in range(10)]
    assert run(rules.structuring, spread) == [] and run(rules.structuring, small) == []


# -- team structuring (owner level) -----------------------------------------------------

def test_team_structuring_fires_across_agents_of_one_owner():
    ts = [
        txn("agent_001", "m_newshub", usd("1.90"), START),
        txn("agent_003", "m_newshub", usd("1.85"), START + H),
        txn("agent_003", "m_newshub", usd("1.80"), START + 2 * H),
    ]
    assert run(rules.structuring, ts[:1]) == []  # no single agent hits the count
    alerts = run(rules.team_structuring, ts)
    assert len(alerts) == 1 and alerts[0].subject_id == "user_growth_lead"
    assert alerts[0].facts["agents"] == ["agent_001", "agent_003"]


def test_team_structuring_quiet_across_different_owners():
    ts = [
        txn("agent_001", "m_newshub", usd("1.90"), START),
        txn("agent_002", "m_finstream", usd("4.50"), START + H),  # other owner
        txn("agent_003", "m_newshub", usd("1.80"), START + 2 * H),
    ]
    assert run(rules.team_structuring, ts) == []


# -- velocity spike -------------------------------------------------------------------

def test_velocity_spike_fires_against_baseline():
    base = [txn("agent_001", "m_newshub", usd("0.002"), START + i * 4 * H) for i in range(42)]  # ~1 per 4h for a week
    burst_start = START + 8 * D
    burst = [txn("agent_001", "m_newshub", usd("0.002"), burst_start + i * 2 * M) for i in range(12)]
    alerts = run(rules.velocity_spike, base + burst)
    assert len(alerts) == 1 and burst[-1].txn_id in alerts[0].txn_ids


def test_velocity_spike_quiet_for_steady_busy_agent():
    steady = [txn("agent_001", "m_newshub", usd("0.002"), START + i * 4 * M) for i in range(15 * 24 * 8)]
    assert run(rules.velocity_spike, steady) == []


def test_velocity_spike_needs_history():
    burst = [txn("agent_001", "m_newshub", usd("0.002"), START + i * M) for i in range(12)]
    assert run(rules.velocity_spike, burst) == []


# -- rapid fire -------------------------------------------------------------------------

def test_rapid_fire_fires():
    ts = [txn("agent_002", "m_finstream", usd("0.005"), START + i * 3 * S) for i in range(15)]
    assert len(run(rules.rapid_fire, ts)) == 1


def test_rapid_fire_quiet_below_count():
    ts = [txn("agent_002", "m_finstream", usd("0.005"), START + i * 5 * S) for i in range(14)]
    assert run(rules.rapid_fire, ts) == []


# -- round amounts ---------------------------------------------------------------------------

def test_round_amounts_fires():
    ts = [txn("agent_002", "m_computemesh", usd(a), START + i * H) for i, a in enumerate((10, 20, 50))]
    assert len(run(rules.round_amounts, ts)) == 1


def test_round_amounts_quiet_for_odd_or_tiny_amounts():
    odd = [txn("agent_002", "m_computemesh", usd(a), START + i * H) for i, a in enumerate(("9.99", "21.37", "50.01"))]
    tiny = [txn("agent_002", "m_computemesh", usd(1), START + i * H) for i in range(5)]  # $1 is not a multiple of $10
    assert run(rules.round_amounts, odd) == [] and run(rules.round_amounts, tiny) == []


# -- look-alike merchants ----------------------------------------------------------------------

def test_lookalike_alert_fires():
    alerts = run(rules.lookalike_merchants, [txn("agent_001", "m_fake_news", usd("0.002"), START)])
    assert len(alerts) == 1 and alerts[0].facts["resembles"] == "m_newshub"


def test_lookalike_quiet_for_trusted_and_unrelated():
    ts = [txn("agent_001", "m_newshub", usd("0.002"), START), txn("agent_001", "m_newco", usd("0.002"), START)]
    assert run(rules.lookalike_merchants, ts) == []


def test_homoglyph_skeletons():
    assert skeleton("ΝewsΗub") == skeleton("NewsHub")  # Greek capitals
    assert skeleton("PixeIMint") == skeleton("PixelMint")  # capital I for l
    assert skeleton("C0deSandb0x") == skeleton("CodeSandbox")
    assert skeleton("Weather-Corp", strip_filler=False) == skeleton("WeatherCorp")
    weather = Merchant("m_weathercorp", "WeatherCorp", "data")
    for fake in ("Weather-Corp LLC", "WeatherCorp Billing", "VVeatherCorp"):
        assert find_lookalike(Merchant("m_x", fake, "data", trusted=False), [weather]) is not None, fake


def test_short_names_are_not_confused():
    trusted = [Merchant("m_box", "Box", "saas")]
    assert find_lookalike(Merchant("m_fox", "Fox", "saas", trusted=False), trusted) is None


# -- new merchant burst ---------------------------------------------------------------------------

def test_new_merchant_burst_fires_for_established_agent():
    history = [txn("agent_001", "m_newshub", usd("0.002"), START + i * D) for i in range(5)]
    burst = [txn("agent_001", f"m_new{i}", usd("0.002"), START + 6 * D + i * H) for i in range(3)]
    alerts = run(rules.new_merchant_burst, history + burst)
    assert len(alerts) == 1 and alerts[0].facts["merchants"] == ["m_new0", "m_new1", "m_new2"]


def test_new_merchant_burst_quiet_for_brand_new_agent_or_spread_out():
    brand_new = [txn("agent_001", f"m_new{i}", usd("0.002"), START + i * H) for i in range(4)]
    history = [txn("agent_001", "m_newshub", usd("0.002"), START)]
    spread = [txn("agent_001", f"m_new{i}", usd("0.002"), START + (3 + 2 * i) * D) for i in range(3)]
    assert run(rules.new_merchant_burst, brand_new) == []
    assert run(rules.new_merchant_burst, history + spread) == []


# -- dormant then active ------------------------------------------------------------------------------

def test_dormant_then_active_fires():
    ts = [txn("agent_003", "m_newshub", usd("0.002"), START)]
    ts += [txn("agent_003", "m_newshub", usd("0.002"), START + 20 * D + i * H) for i in range(3)]
    alerts = run(rules.dormant_then_active, ts)
    assert len(alerts) == 1 and alerts[0].facts["idle_days"] == 20


def test_dormant_then_active_quiet_for_short_gap_or_single_payment():
    short_gap = [txn("agent_003", "m_newshub", usd("0.002"), START)]
    short_gap += [txn("agent_003", "m_newshub", usd("0.002"), START + 10 * D + i * H) for i in range(3)]
    one_after = [txn("agent_003", "m_newshub", usd("0.002"), START), txn("agent_003", "m_newshub", usd("0.002"), START + 20 * D)]
    assert run(rules.dormant_then_active, short_gap) == [] and run(rules.dormant_then_active, one_after) == []


# -- fan-in ------------------------------------------------------------------------------------------------

def test_fan_in_fires_for_untrusted_merchant():
    ts = [txn(a, "m_newco", usd("0.50"), START + i * H) for i, a in enumerate(("agent_001", "agent_002", "agent_003"))]
    assert len(run(rules.fan_in, ts)) == 1


def test_fan_in_quiet_for_trusted_merchant_or_few_agents():
    trusted = [txn(a, "m_newshub", usd("0.002"), START + i * H) for i, a in enumerate(("agent_001", "agent_002", "agent_003"))]
    two = [txn(a, "m_newco", usd("0.50"), START + i * H) for i, a in enumerate(("agent_001", "agent_002"))]
    assert run(rules.fan_in, trusted) == [] and run(rules.fan_in, two) == []


# -- high-risk category ------------------------------------------------------------------------------------

def test_high_risk_category_fires():
    assert len(run(rules.high_risk_category, [txn("agent_002", "m_gift", usd(25), START)])) == 1


def test_high_risk_category_quiet_for_normal_category():
    assert run(rules.high_risk_category, [txn("agent_002", "m_finstream", usd(25), START)]) == []


# -- monitor --------------------------------------------------------------------------------------------------

def test_rule_list_is_complete():
    assert {r.__name__ for r in rules.ALL_RULES} == {
        "structuring", "team_structuring", "velocity_spike", "rapid_fire", "round_amounts", "lookalike_merchants",
        "new_merchant_burst", "dormant_then_active", "fan_in", "high_risk_category"}


def test_monitor_reports_each_alert_once_and_grows_it():
    mon = AmlMonitor(reg())
    first = [txn("agent_001", "m_newshub", usd("1.95"), START + i * H) for i in range(3)]
    new1 = mon.scan(first)
    extra = txn("agent_001", "m_newshub", usd("1.90"), START + 3 * H)
    new2 = mon.scan(first + [extra])
    assert len(new1) == 1 and new2 == []
    assert extra.txn_id in mon.alerts[new1[0].alert_id].txn_ids


def test_clean_traffic_raises_no_alerts():
    ts = []
    for day in range(10):
        for i, (agent, merchant, price) in enumerate((("agent_001", "m_newshub", "0.002"), ("agent_002", "m_finstream", "0.005"),
                                                      ("agent_003", "m_pixelmint", "0.020"))):
            ts += [txn(agent, merchant, usd(price), START + day * D + (i * 7 + k * 37) * M) for k in range(8)]
    assert AmlMonitor(reg()).scan(ts) == []


def test_alerts_cite_only_ledger_transactions_end_to_end(clock):
    g = make_guard(clock)
    g.registry.agents["agent_001"] = replace(g.registry.agents["agent_001"], per_txn_limit=usd(5))
    for amt in ("1.95", "1.90", "1.85"):
        assert g.submit_payment(req(amount=usd(amt))).approved
        clock.advance(hours=1)
    alerts = g.run_monitoring()
    assert [a.rule for a in alerts] == [R.AML_STRUCTURING]
    ledger_ids = {t.txn_id for t in g.ledger.transactions()}
    assert all(tid in ledger_ids for a in alerts for tid in a.txn_ids)
    assert g.audit.by_type(EventType.AML_ALERT)
