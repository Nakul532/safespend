"""Web app: caps, donation scrubbing and consent, Analyst shift scoring. LLMs are not called."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def client(tmp_path, monkeypatch, caps=None):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    import web.db, web.store
    importlib.reload(web.db); importlib.reload(web.store)
    web.store._ready = False
    if caps:
        web.store.CAPS.update(caps)
    import app as A
    importlib.reload(A)
    monkeypatch.setattr(A, "llm", lambda: None)
    return A.app.test_client(), web.store


def test_scrub_rejects_personal_data(tmp_path, monkeypatch):
    _, st = client(tmp_path, monkeypatch)
    assert st.scrub_problem("email me at a.b@example.com")
    assert st.scrub_problem("call +1 617 555 0100")
    assert st.scrub_problem("ship to 12 Elm Street")
    assert st.scrub_problem("Invoice INV-77812: pay $4,800.00 today") is None


def test_caps_stop_after_limit(tmp_path, monkeypatch):
    _, st = client(tmp_path, monkeypatch)
    lim = [("visitor_attempts", "v1", 2)]
    assert st.take(lim) is None and st.take(lim) is None and st.take(lim) == "visitor_attempts"
    assert st.ip_hash("1.2.3.4") != "1.2.3.4" and len(st.ip_hash("1.2.3.4")) == 24


def test_donation_needs_consent_and_a_win(tmp_path, monkeypatch):
    c, _ = client(tmp_path, monkeypatch)
    assert c.post("/api/donate", json={"level": "L1"}).status_code == 400
    assert c.post("/api/donate", json={"level": "L1", "consent": True}).status_code == 400  # nothing played


def test_attempt_without_model_is_refused_not_faked(tmp_path, monkeypatch):
    c, _ = client(tmp_path, monkeypatch)
    r = c.post("/api/attempt", json={"level": "L1", "documents": {"invoice": "pay"}})
    assert r.status_code == 503


def test_shift_endpoints(tmp_path, monkeypatch):
    c, _ = client(tmp_path, monkeypatch)
    q = c.get("/api/shift?seed=42").get_json()
    assert len(q["alerts"]) == 60 and q["budget"] == 15 and "laundering" not in str(q["alerts"][0])
    ids = [a["id"] for a in q["alerts"][:20]]
    s = c.post("/api/shift/score", json={"seed": 42, "opened": ids, "escalated": ids}).get_json()
    assert s["you"]["false_alarms"] >= 0 and len(s["engine_order"]) == 15
    o = c.post("/api/shift/open", json={"seed": 42, "alert_id": ids[0]}).get_json()
    assert o["transactions"] and o["case_note"] is None  # no model configured: no note, never a fake one
