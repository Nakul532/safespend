"""Look-alike merchant detection: homoglyphs plus edit distance.

A name is reduced to a "skeleton": Unicode-normalised, lower-cased,
confusable characters mapped to Latin look-alikes (Cyrillic 'о' -> 'o',
digit '0' -> 'o', 'rn' -> 'm'), punctuation removed. Two merchants look
alike when their skeletons are equal or within a small edit distance.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from .models import Merchant

# Single characters that render like a Latin letter.
_HOMOGLYPHS = {
    # Cyrillic
    "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o",
    "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ї": "i", "ј": "j",
    "ѕ": "s", "ԁ": "d", "ɡ": "g", "һ": "h", "ӏ": "l", "ԛ": "q", "ԝ": "w",
    # Greek
    "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o",
    "ρ": "p", "τ": "t", "υ": "u", "χ": "x", "ω": "w",
    # Digits and symbols used as letters
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s", "|": "l",
    # Latin letters commonly swapped
    "i": "l",
}
# Capital letters that look Latin, mapped before lower-casing (Greek 'Ν' lower-cases to 'ν', which looks like 'v').
_UPPER_HOMOGLYPHS = {
    "Α": "a", "Β": "b", "Ε": "e", "Ζ": "z", "Η": "h", "Ι": "l", "Κ": "k", "Μ": "m", "Ν": "n", "Ο": "o",
    "Ρ": "p", "Τ": "t", "Υ": "y", "Χ": "x",
    "А": "a", "В": "b", "Е": "e", "К": "k", "М": "m", "Н": "h", "О": "o", "Р": "p", "С": "c", "Т": "t", "Х": "x",
}
# Multi-character sequences that render like one letter.
_SEQUENCES = (("rn", "m"), ("vv", "w"), ("cl", "d"))


# Words that impersonators append to a real brand ("NewsHub Inc", "NewsHub Payments").
_FILLER_WORDS = frozenset({
    "inc", "llc", "ltd", "limited", "corp", "corporation", "co", "company", "gmbh", "plc", "sa",
    "official", "api", "apis", "billing", "payments", "pay", "support", "secure", "hq", "the",
})


def _strip_filler(name: str) -> str:
    words = [w for w in re.split(r"[^\w]+", unicodedata.normalize("NFKC", name).casefold()) if w]
    kept = [w for w in words if w not in _FILLER_WORDS]
    return " ".join(kept or words)


def skeleton(name: str, strip_filler: bool = True) -> str:
    text = unicodedata.normalize("NFKC", name)
    text = "".join(_UPPER_HOMOGLYPHS.get(c, c) for c in text)
    text = _strip_filler(text) if strip_filler else text.casefold()
    # Strip accents: é -> e
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = "".join(_HOMOGLYPHS.get(c, c) for c in text)
    text = "".join(c for c in text if c.isalnum())
    for seq, repl in _SEQUENCES:
        text = text.replace(seq, repl)
    return text


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass(frozen=True)
class LookalikeMatch:
    merchant_id: str
    merchant_name: str
    resembles_id: str
    resembles_name: str
    distance: int  # edit distance between skeletons (0 = identical after normalisation)
    contains_brand: bool = False  # the trusted name appears inside this one


def find_lookalike(merchant: Merchant, trusted: Iterable[Merchant], max_distance: int = 2) -> LookalikeMatch | None:
    """Return the closest trusted merchant this one imitates, or None.

    A trusted merchant never imitates another. Short names get a tighter
    limit so that, for example, 'Box' and 'Fox' are not confused.
    """
    if merchant.trusted:
        return None
    # Compare with and without filler words, so both "NewsHub Inc" and "Weather-Corp" are caught.
    mine = {skeleton(merchant.name), skeleton(merchant.name, strip_filler=False)}
    best: LookalikeMatch | None = None
    for t in trusted:
        if t.merchant_id == merchant.merchant_id:
            continue
        theirs = {skeleton(t.name), skeleton(t.name, strip_filler=False)}
        for sk in mine:
            for tsk in theirs:
                shortest = min(len(sk), len(tsk))
                limit = max_distance if shortest >= 6 else min(max_distance, 1) if shortest >= 4 else 0
                d = levenshtein(sk, tsk)
                contains = len(tsk) >= 6 and tsk in sk
                if (d <= limit or contains) and (best is None or d < best.distance):
                    best = LookalikeMatch(merchant.merchant_id, merchant.name, t.merchant_id, t.name, d, contains)
    return best
