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


def make_checker(run_tag: str, *, llm: bool = True):
    from safespend.injection import InjectionChecker
    from safespend.llm import GroqClient
    client = None
    if llm:
        load_env()
        client = GroqClient(default_model=MODEL)  # key from GROQ_API_KEY
    return InjectionChecker(client, model=MODEL, cache_dir=CACHE / "injection", run_tag=run_tag, min_interval_s=2.5)
