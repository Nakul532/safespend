"""Persistence for the web app: LLM caches, game attempts, caps, the global vault, and consented donations.
No personal data: visitors are a random cookie id; IP addresses are only ever stored as a salted daily hash
in the caps table, never next to an attempt or a donation."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets

from . import db

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS attempts (session TEXT, level TEXT, n INTEGER, created TEXT, documents TEXT, proposals TEXT, "
    "note TEXT, PRIMARY KEY (session, level, n))",
    "CREATE TABLE IF NOT EXISTS counters (day TEXT, scope TEXT, k TEXT, n INTEGER, PRIMARY KEY (day, scope, k))",
    "CREATE TABLE IF NOT EXISTS vault (id INTEGER PRIMARY KEY, protected INTEGER, lost INTEGER, attempts INTEGER, caught INTEGER)",
    "CREATE TABLE IF NOT EXISTS donations (id TEXT PRIMARY KEY, created TEXT, level TEXT, policy_version TEXT, documents TEXT, "
    "proposals TEXT, outcome TEXT, status TEXT)",
]

CAPS = {"visitor_attempts": int(os.environ.get("VISITOR_DAILY_ATTEMPTS", 30)),
        "ip_attempts": int(os.environ.get("IP_DAILY_ATTEMPTS", 60)),
        "site_attempts": int(os.environ.get("SITE_DAILY_ATTEMPTS", 1500)),
        "visitor_notes": int(os.environ.get("VISITOR_DAILY_NOTES", 40)),
        "site_notes": int(os.environ.get("SITE_DAILY_NOTES", 1500)),
        "visitor_donations": 3, "monthly_donations": 200}

_ready = False


def conn():
    global _ready
    c = db.connect()
    if not _ready:
        if hasattr(c, "execute_batch"):
            c.execute_batch([(s, ()) for s in SCHEMA])
        else:
            for s in SCHEMA:
                c.execute(s)
            c.commit()
        _ready = True
    return c


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


class KV:
    """get/put cache used by the LLM checks, the agent and the investigator."""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def get(self, k, default=None):
        row = conn().execute("SELECT v FROM kv WHERE k = ?", (self.prefix + k,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, k, v):
        c = conn()
        c.execute("INSERT OR REPLACE INTO kv (k, v) VALUES (?, ?)", (self.prefix + k, json.dumps(v)))
        c.commit()


def ip_hash(ip: str) -> str:
    salt = os.environ.get("CAP_SALT", "dev-salt") + today()
    return hashlib.sha256((salt + (ip or "")).encode()).hexdigest()[:24]


def take(scope_limits: list[tuple[str, str, int]]) -> str | None:
    """Check then increment several daily counters. Returns the name of the first exhausted cap, or None."""
    c, d = conn(), today()
    for scope, key, limit in scope_limits:
        row = c.execute("SELECT n FROM counters WHERE day=? AND scope=? AND k=?", (d, scope, key)).fetchone()
        if row and row[0] >= limit:
            return scope
    for scope, key, _ in scope_limits:
        c.execute("INSERT INTO counters (day, scope, k, n) VALUES (?, ?, ?, 1) "
                  "ON CONFLICT(day, scope, k) DO UPDATE SET n = n + 1", (d, scope, key))
    c.commit()
    return None


def used(scope: str, key: str) -> int:
    row = conn().execute("SELECT n FROM counters WHERE day=? AND scope=? AND k=?", (today(), scope, key)).fetchone()
    return row[0] if row else 0


def attempts(session: str, level: str) -> list[dict]:
    rows = conn().execute("SELECT n, documents, proposals, note FROM attempts WHERE session=? AND level=? ORDER BY n",
                          (session, level)).fetchall()
    return [{"n": r[0], "documents": json.loads(r[1]), "proposals": json.loads(r[2]), "note": r[3]} for r in rows]


def add_attempt(session: str, level: str, a: dict) -> None:
    c = conn()
    c.execute("INSERT INTO attempts (session, level, n, created, documents, proposals, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (session, level, a["n"], dt.datetime.now(dt.timezone.utc).isoformat(), json.dumps(a["documents"]),
               json.dumps(a["proposals"]), a.get("note") or ""))
    c.commit()


def reset_level(session: str, level: str) -> None:
    c = conn()
    c.execute("DELETE FROM attempts WHERE session=? AND level=?", (session, level))
    c.commit()


def vault_add(protected: int, lost: int, caught: bool) -> None:
    c = conn()
    c.execute("INSERT INTO vault (id, protected, lost, attempts, caught) VALUES (1, ?, ?, 1, ?) ON CONFLICT(id) DO UPDATE SET "
              "protected = protected + excluded.protected, lost = lost + excluded.lost, attempts = attempts + 1, "
              "caught = caught + excluded.caught", (protected, lost, int(caught)))
    c.commit()


def vault() -> dict:
    row = conn().execute("SELECT protected, lost, attempts, caught FROM vault WHERE id = 1").fetchone()
    p, l, a, k = row or (0, 0, 0, 0)
    donated = conn().execute("SELECT COUNT(*) FROM donations WHERE status = 'accepted'").fetchone()[0]
    return {"protected": p, "lost": l, "attempts": a, "caught": k, "donations_accepted": donated}


# -- donations (opt-in, moderated) ------------------------------------------------------

_PII = [re.compile(p, re.I) for p in (
    r"[\w.+-]+@[\w-]+\.[\w.]+",  # email
    r"(\+?\d[\s().-]?){10,}",  # phone or long digit runs (cards, accounts)
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",  # IBAN-like
    r"\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd)\b",  # street address
    r"\b(ssn|social security|passport|date of birth|dob)\b",
)]
_BLOCK = re.compile(r"\b(kill|bomb|terror|nazi|rape)\b", re.I)


def scrub_problem(text: str) -> str | None:
    if any(p.search(text) for p in _PII):
        return "It looks like it contains personal information (an email, phone number, account or address)."
    if _BLOCK.search(text):
        return "It contains content we don't store."
    return None


def donate(level: str, policy_version: str, documents: dict, proposals: list, outcome: str) -> tuple[str | None, str | None]:
    text = "\n".join(str(v) for v in documents.values())
    problem = scrub_problem(text)
    if problem:
        return None, problem
    month = today()[:7]
    n = conn().execute("SELECT COUNT(*) FROM donations WHERE substr(created, 1, 7) = ?", (month,)).fetchone()[0]
    if n >= CAPS["monthly_donations"]:
        return None, "This month's donation limit is reached. Thank you anyway."
    sid = "D-" + secrets.token_hex(4).upper()
    c = conn()
    c.execute("INSERT INTO donations (id, created, level, policy_version, documents, proposals, outcome, status) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_review')",
              (sid, dt.datetime.now(dt.timezone.utc).isoformat(), level, policy_version,
               json.dumps({k: v[:2000] for k, v in documents.items()}), json.dumps(proposals), outcome))
    c.commit()
    return sid, None


def delete_donation(sid: str) -> bool:
    c = conn()
    cur = c.execute("DELETE FROM donations WHERE id = ?", (sid,))
    c.commit()
    return cur.rowcount > 0
