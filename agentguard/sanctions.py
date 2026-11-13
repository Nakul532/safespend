"""Sanctions screening interface.

Stage 1 ships the interface and a simple exact-match screener for tests.
The real OFAC SDN list with fuzzy matching arrives in a later stage.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True)
class SanctionsMatch:
    screened_name: str
    listed_name: str
    list_name: str
    list_date: str


class SanctionsScreener(Protocol):
    def screen(self, name: str) -> SanctionsMatch | None: ...


class NullScreener:
    """Screens nothing. Use only where sanctions screening is out of scope."""

    def screen(self, name: str) -> SanctionsMatch | None:
        return None


def _norm(name: str) -> str:
    name = unicodedata.normalize("NFKC", name).casefold()
    return re.sub(r"[^0-9a-z]+", " ", name).strip()


class ExactListScreener:
    def __init__(self, names: Iterable[str], list_name: str, list_date: str) -> None:
        self._names = {_norm(n): n for n in names}
        self.list_name = list_name
        self.list_date = list_date

    def screen(self, name: str) -> SanctionsMatch | None:
        listed = self._names.get(_norm(name))
        if listed is None:
            return None
        return SanctionsMatch(name, listed, self.list_name, self.list_date)


# ---------------------------------------------------------------------------
# ADDED AFTER THE RED-TEAM LOCK (Stage 3): fuzzy screening.
# Tuned on the builder's dev list (eval/dev/sanctions_dev.json), not on locked scenarios.
# ---------------------------------------------------------------------------

_CYRILLIC = dict(zip("абвгдезийклмнопрстуфхцыэюя", ["a", "b", "v", "g", "d", "e", "z", "i", "y", "k", "l", "m", "n", "o",
                                                     "p", "r", "s", "t", "u", "f", "h", "ts", "y", "e", "yu", "ya"]))
_CYRILLIC.update({"ж": "zh", "ч": "ch", "ш": "sh", "щ": "shch", "ё": "e", "ъ": "", "ь": ""})
_LEGAL_SUFFIXES = frozenset({"llc", "ltd", "limited", "inc", "co", "corp", "company", "sa", "fze", "fzco", "plc",
                             "gmbh", "ag", "jsc", "ooo", "oao", "pjsc", "bv", "nv", "srl", "spa"})
# Spelling variants common in transliteration, applied to both sides.
_TRANSLIT = (("yy", "y"), ("iy", "y"), ("ij", "y"), ("kh", "h"), ("ph", "f"), ("ck", "k"), ("c", "k"),
             ("w", "v"), ("ou", "u"), ("oo", "u"), ("ee", "i"), ("q", "k"), ("x", "ks"))


def _fuzzy_tokens(name: str) -> list[str]:
    text = unicodedata.normalize("NFKC", name).casefold()
    text = "".join(_CYRILLIC.get(ch, ch) for ch in text)
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    words = [w for w in re.split(r"[^0-9a-z]+", text) if w and w not in _LEGAL_SUFFIXES and w not in ("al", "el")]
    out = []
    for w in words:
        for a, b in _TRANSLIT:
            w = w.replace(a, b)
        out.append(w)
    return out


def _ratio(a: str, b: str) -> float:
    from .lookalike import levenshtein
    if not a and not b:
        return 1.0
    return 1 - levenshtein(a, b) / max(len(a), len(b))


def name_similarity(candidate: str, listed: str) -> float:
    """0..1. Each listed word is matched to its closest candidate word (order ignored);
    extra candidate words beyond one lower the score."""
    c, l = _fuzzy_tokens(candidate), _fuzzy_tokens(listed)
    if not c or not l:
        return 0.0
    per_word = [max(_ratio(lw, cw) for cw in c) for lw in l]
    score = sum(per_word) / len(per_word)
    extra = max(0, len(c) - len(l) - 1)
    return max(0.0, score - 0.1 * extra)


class FuzzyScreener:
    def __init__(self, names: Iterable[str], list_name: str, list_date: str, threshold: float = 0.85) -> None:
        self._names = list(names)
        self.list_name = list_name
        self.list_date = list_date
        self.threshold = threshold

    def best(self, name: str) -> tuple[str, float]:
        return max(((n, name_similarity(name, n)) for n in self._names), key=lambda x: x[1], default=("", 0.0))

    def screen(self, name: str) -> SanctionsMatch | None:
        listed, score = self.best(name)
        if score >= self.threshold:
            return SanctionsMatch(name, listed, self.list_name, self.list_date)
        return None
