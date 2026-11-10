"""Injectable UTC clock.

Every time-window rule (budgets, velocity, approvals, AML) reads time from a
Clock, never from datetime.now() directly. Tests use ManualClock.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol


def ensure_utc(dt: datetime) -> datetime:
    """Reject naive datetimes and normalise aware ones to UTC."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("naive datetime: all AgentGuard times must be timezone-aware UTC")
    return dt.astimezone(timezone.utc)


def utc_day_start(dt: datetime) -> datetime:
    """Midnight UTC of the day containing ``dt`` (daily budgets reset here)."""
    dt = ensure_utc(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class ManualClock:
    """A clock that only moves when told to. Used in tests and replays."""

    def __init__(self, start: datetime) -> None:
        self._now = ensure_utc(start)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: float) -> datetime:
        delta = timedelta(**kwargs)
        if delta < timedelta(0):
            raise ValueError("ManualClock cannot go backwards")
        self._now += delta
        return self._now

    def set(self, dt: datetime) -> None:
        dt = ensure_utc(dt)
        if dt < self._now:
            raise ValueError("ManualClock cannot go backwards")
        self._now = dt
