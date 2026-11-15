"""LlmClient (no network), money, and the injectable clock."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from safespend.clock import ManualClock, SystemClock, ensure_utc, utc_day_start
from safespend.llm import (
    GroqClient, LlmConfigError, LlmError, LlmRateLimited, MockLlmClient, OpenRouterClient, drop_sentences_with_digits,
)
from safespend.money import fmt_usd, usd

MSGS = [{"role": "user", "content": "hello"}]
OK = {"model": "openai/gpt-oss-120b", "choices": [{"message": {"content": "hi"}}],
      "usage": {"prompt_tokens": 3, "completion_tokens": 1}}


class FakeTransport:
    def __init__(self, status=200, data=None):
        self.status, self.data, self.calls = status, data if data is not None else OK, []

    def __call__(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "body": body})
        return self.status, self.data


# -- LLM clients ------------------------------------------------------------------

def test_groq_request_shape_and_response():
    t = FakeTransport()
    r = GroqClient(api_key="test-key", transport=t).complete(MSGS, json_mode=True)
    call = t.calls[0]
    assert call["url"].startswith("https://api.groq.com/")
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["body"]["model"] == "openai/gpt-oss-120b" and call["body"]["temperature"] == 0.0
    assert call["body"]["response_format"] == {"type": "json_object"}
    assert "provider" not in call["body"]
    assert (r.text, r.provider, r.input_tokens, r.output_tokens) == ("hi", "groq", 3, 1)


def test_openrouter_is_pinned_to_groq_without_fallbacks():
    t = FakeTransport()
    OpenRouterClient(api_key="test-key", transport=t).complete(MSGS, model="openai/gpt-oss-20b")
    body = t.calls[0]["body"]
    assert t.calls[0]["url"].startswith("https://openrouter.ai/")
    assert body["provider"] == {"order": ["Groq"], "allow_fallbacks": False}
    assert body["model"] == "openai/gpt-oss-20b"


def test_keys_come_from_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(LlmConfigError):
        GroqClient(transport=FakeTransport())
    with pytest.raises(LlmConfigError):
        OpenRouterClient(transport=FakeTransport())
    monkeypatch.setenv("GROQ_API_KEY", "from-env")
    t = FakeTransport()
    GroqClient(transport=t).complete(MSGS)
    assert t.calls[0]["headers"]["Authorization"] == "Bearer from-env"


def test_rate_limit_and_errors_raise():
    with pytest.raises(LlmRateLimited):
        GroqClient(api_key="k", transport=FakeTransport(429, {})).complete(MSGS)
    with pytest.raises(LlmError, match="HTTP 500"):
        GroqClient(api_key="k", transport=FakeTransport(500, {"error": {"message": "boom"}})).complete(MSGS)
    with pytest.raises(LlmError, match="unexpected"):
        GroqClient(api_key="k", transport=FakeTransport(200, {"choices": []})).complete(MSGS)


def test_mock_scripted_and_recorded():
    m = MockLlmClient(["one", "two"])
    assert [m.complete(MSGS).text, m.complete(MSGS, max_tokens=9).text] == ["one", "two"]
    assert m.calls[1]["max_tokens"] == 9
    with pytest.raises(LlmError):
        m.complete(MSGS)


def test_mock_function_replies():
    m = MockLlmClient(lambda msgs: msgs[-1]["content"].upper())
    assert m.complete(MSGS).text == "HELLO"


def test_no_gemini_left_in_codebase():
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "safespend"
    assert not [p for p in src.rglob("*.py") if "gemini" in p.read_text().lower() or "generativeai" in p.read_text()]


# -- LLM output rule: drop sentences with digits ------------------------------------------

def test_sentences_with_digits_dropped():
    text, dropped = drop_sentences_with_digits("The agent paid a new merchant. It spent 40 dollars. Review it!")
    assert text == "The agent paid a new merchant. Review it!" and dropped == 1


def test_unicode_digits_dropped_and_clean_text_kept():
    assert drop_sentences_with_digits("Paid ٣ times. Looks odd.") == ("Looks odd.", 1)
    assert drop_sentences_with_digits("No numbers here. None at all.") == ("No numbers here. None at all.", 0)


# -- money ---------------------------------------------------------------------------------

def test_usd_exact_and_rejects_float():
    assert usd("0.001") == 1_000 and usd(5) == 5_000_000 and usd("0.000001") == 1
    assert usd("0.1") + usd("0.2") == usd("0.3")
    with pytest.raises(TypeError):
        usd(0.1)
    with pytest.raises(ValueError):
        usd("0.0000001")
    with pytest.raises(ValueError):
        usd("abc")


def test_fmt_usd():
    assert fmt_usd(usd("0.002")) == "$0.00"
    assert fmt_usd(usd("0.005")) == "$0.01"  # half up
    assert fmt_usd(usd("3844.388789")) == "$3,844.39"
    assert fmt_usd(0) == "$0.00" and fmt_usd(-usd("0.004")) == "$0.00"
    assert fmt_usd(usd(5)) == "$5.00"
    assert fmt_usd(usd("1234.5")) == "$1,234.50"
    assert fmt_usd(-usd("0.25")) == "-$0.25"


# -- clock -----------------------------------------------------------------------------------

def test_manual_clock_moves_only_forward():
    c = ManualClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
    c.advance(hours=2)
    assert c.now() == datetime(2026, 1, 1, 2, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        c.advance(seconds=-1)
    with pytest.raises(ValueError):
        c.set(datetime(2025, 1, 1, tzinfo=timezone.utc))


def test_naive_datetimes_rejected_and_offsets_normalised():
    with pytest.raises(ValueError):
        ManualClock(datetime(2026, 1, 1))
    est = timezone(timedelta(hours=-5))
    assert ensure_utc(datetime(2026, 1, 1, 22, tzinfo=est)) == datetime(2026, 1, 2, 3, tzinfo=timezone.utc)
    assert utc_day_start(datetime(2026, 1, 1, 22, tzinfo=est)) == datetime(2026, 1, 2, tzinfo=timezone.utc)


def test_system_clock_is_utc_aware():
    assert SystemClock().now().tzinfo is not None


def test_no_direct_wall_clock_reads_in_time_logic():
    """Time windows must use the injected Clock. Only clock.py may read the wall clock."""
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "safespend"
    offenders = [p.name for p in src.rglob("*.py") if p.name != "clock.py"
                 and any(s in p.read_text() for s in ("datetime.now(", "datetime.utcnow(", "time.time("))]
    assert offenders == []
