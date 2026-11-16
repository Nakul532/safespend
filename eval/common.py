"""Shared helpers for Stage 3 evaluations."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "eval" / "cache"
MODEL = "openai/gpt-oss-120b"


def load_env(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines into os.environ without printing anything."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def eval_client():
    """Evals use OpenRouter (OPENROUTER_API_KEY), pinned to Groq with fallbacks off, so they never share the live site's
    Groq free-key rate limit (decision 2026-11-15)."""
    from safespend.llm.client import OpenRouterClient
    load_env()
    return OpenRouterClient(default_model=MODEL)


def make_checker(run_tag: str, *, llm: bool = True):
    from safespend.injection import InjectionChecker
    client = None
    if llm:
        client = eval_client()  # OpenRouter pinned to Groq (was GroqClient before 2026-11-15)
    return InjectionChecker(client, model=MODEL, cache_dir=CACHE / "injection", run_tag=run_tag, min_interval_s=2.5)
