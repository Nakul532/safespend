"""Output rules for LLM-written text.

Every number on screen comes from code. Any LLM-written sentence that
contains a digit is dropped before display.
"""
from __future__ import annotations

import re
import unicodedata

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _has_digit(text: str) -> bool:
    # Catches ASCII digits and other Unicode digits (e.g. Arabic-Indic, full-width).
    return any(unicodedata.category(ch) == "Nd" for ch in text)


def drop_sentences_with_digits(text: str) -> tuple[str, int]:
    """Return (cleaned text, number of sentences dropped)."""
    kept: list[str] = []
    dropped = 0
    for sentence in _SENTENCE_END.split(text.strip()):
        if not sentence:
            continue
        if _has_digit(sentence):
            dropped += 1
        else:
            kept.append(sentence)
    return " ".join(kept), dropped
