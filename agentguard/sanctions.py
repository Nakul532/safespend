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
