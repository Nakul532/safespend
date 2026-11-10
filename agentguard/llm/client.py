"""LlmClient: one interface, three implementations.

- GroqClient: the live site (free key, GROQ_API_KEY).
- OpenRouterClient: evals (prepaid, OPENROUTER_API_KEY), pinned to the Groq
  provider with fallbacks off, so results come from the same model host.
- MockLlmClient: tests. Scripted replies, no network.

Keys are read only from environment variables. In AgentGuard the LLM never
decides anything: its output is advice that deterministic code checks.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

DEFAULT_MODEL = "openai/gpt-oss-120b"
SMALL_MODEL = "openai/gpt-oss-20b"

Message = Mapping[str, str]  # {"role": "system"|"user"|"assistant", "content": "..."}
# A transport takes (url, headers, json_body, timeout) and returns (status, json_response).
Transport = Callable[[str, Mapping[str, str], dict[str, Any], float], tuple[int, dict[str, Any]]]


class LlmError(Exception):
    pass


class LlmConfigError(LlmError):
    pass


class LlmRateLimited(LlmError):
    pass


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


class LlmClient(Protocol):
    def complete(
        self,
        messages: Sequence[Message],
        *,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> LlmResponse: ...


def urllib_transport(url: str, headers: Mapping[str, str], body: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {"error": {"message": str(exc)}}
        return exc.code, payload


class _OpenAICompatibleClient:
    provider = "base"
    url = ""
    env_var = ""

    def __init__(self, api_key: str | None = None, *, transport: Transport | None = None,
                 default_model: str = DEFAULT_MODEL, timeout: float = 30.0) -> None:
        key = api_key if api_key is not None else os.environ.get(self.env_var, "")
        if not key:
            raise LlmConfigError(f"{self.env_var} is not set")
        self._key = key
        self._transport = transport or urllib_transport
        self.default_model = default_model
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}

    def _body(self, messages: Sequence[Message], model: str, max_tokens: int, temperature: float, json_mode: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "messages": [dict(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        return body

    def complete(self, messages: Sequence[Message], *, model: str | None = None, max_tokens: int = 512,
                 temperature: float = 0.0, json_mode: bool = False) -> LlmResponse:
        body = self._body(messages, model or self.default_model, max_tokens, temperature, json_mode)
        start = time.perf_counter()
        status, data = self._transport(self.url, self._headers(), body, self.timeout)
        latency = (time.perf_counter() - start) * 1000
        if status == 429:
            raise LlmRateLimited(f"{self.provider} rate limit")
        if status != 200:
            msg = (data.get("error") or {}).get("message", "unknown error") if isinstance(data, dict) else "unknown error"
            raise LlmError(f"{self.provider} returned HTTP {status}: {msg}")
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"{self.provider} returned an unexpected response shape") from exc
        usage = data.get("usage") or {}
        return LlmResponse(
            text=text,
            model=data.get("model", body["model"]),
            provider=self.provider,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency,
            raw=data,
        )


class GroqClient(_OpenAICompatibleClient):
    provider = "groq"
    url = "https://api.groq.com/openai/v1/chat/completions"
    env_var = "GROQ_API_KEY"


class OpenRouterClient(_OpenAICompatibleClient):
    """OpenRouter, pinned to Groq as the only provider, with fallbacks off."""

    provider = "openrouter"
    url = "https://openrouter.ai/api/v1/chat/completions"
    env_var = "OPENROUTER_API_KEY"

    def _body(self, *args: Any) -> dict[str, Any]:
        body = super()._body(*args)
        body["provider"] = {"order": ["Groq"], "allow_fallbacks": False}
        return body


class MockLlmClient:
    """Deterministic stand-in for tests.

    Give it a list of replies (returned in order) or a function that maps
    messages to a reply. Every call is recorded in .calls.
    """

    provider = "mock"

    def __init__(self, replies: Sequence[str] | Callable[[Sequence[Message]], str] = ("",),
                 model: str = "mock-model") -> None:
        self._replies = replies
        self._i = 0
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def complete(self, messages: Sequence[Message], *, model: str | None = None, max_tokens: int = 512,
                 temperature: float = 0.0, json_mode: bool = False) -> LlmResponse:
        self.calls.append({"messages": [dict(m) for m in messages], "model": model or self.model,
                           "max_tokens": max_tokens, "temperature": temperature, "json_mode": json_mode})
        if callable(self._replies):
            text = self._replies(messages)
        else:
            if self._i >= len(self._replies):
                raise LlmError("MockLlmClient ran out of scripted replies")
            text = self._replies[self._i]
            self._i += 1
        return LlmResponse(text=text, model=model or self.model, provider=self.provider)
