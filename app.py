"""AgentGuard web app (Flask on Vercel). SIMULATED money only.

Pages are static files in web/public. The API runs the real AgentGuard engine on every request.
"""
from __future__ import annotations

import os
import random
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, make_response, request, send_from_directory

from agentguard.investigator import Investigator, evidence
from agentguard.llm import GroqClient
from agentguard.money import fmt_usd
from agentguard.synth import best, generate, ranked, score
from web import store
from web.game.agent import AgentUnavailable, propose
from web.game.levels import ORDER, WORLDS, policy_for
from web.game.play import CHECK_MODEL, reveal, run

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "web" / "public"
app = Flask(__name__, static_folder=None)
MAX_DOC = 2000
SHIFT_BUDGET, SHIFT_SECONDS = 15, 180


def _load_env():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()


def llm():
    return GroqClient(default_model=CHECK_MODEL, timeout=30) if os.environ.get("GROQ_API_KEY") else None


def visitor() -> tuple[str, bool]:
    vid = request.cookies.get("ag_vid")
    if vid and len(vid) == 32:
        return vid, False
    return secrets.token_hex(16), True


def respond(payload, vid_new: tuple[str, bool] | None = None, status=200):
    r = make_response(jsonify(payload), status)
    if vid_new and vid_new[1]:
        r.set_cookie("ag_vid", vid_new[0], max_age=60 * 60 * 24 * 90, samesite="Lax", httponly=True,
                     secure=bool(os.environ.get("VERCEL")))
    return r


def client_ip() -> str:
    return (request.headers.get("x-forwarded-for") or request.remote_addr or "").split(",")[0].strip()


# -- pages ------------------------------------------------------------------------------

@app.get("/")
def home():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/<page>")
def page(page):
    if page in ("play", "shift", "pro", "privacy"):
        return send_from_directory(PUBLIC, f"{page}.html")
    return send_from_directory(PUBLIC, page)


@app.get("/data/<path:p>")
def data(p):
    return send_from_directory(PUBLIC / "data", p)


@app.get("/assets/<path:p>")
def assets(p):
    return send_from_directory(PUBLIC / "assets", p)


# -- Break the bank ----------------------------------------------------------------------

def world_info(w):
    policy, llm_checks, aml = policy_for(w)
    return {"key": w.key, "level": w.level, "title": w.title, "modelled_on": w.modelled_on, "brief": w.brief,
            "defence": w.defence, "lesson": w.lesson, "request": w.request, "target": w.target, "tools": list(w.tools),
            "templates": [{"name": n, "text": t} for n, t in w.templates], "gaps": list(w.gaps),
            "agent": {"name": w.agent.name, "role": w.agent.role, "owner": w.agent.owner_id.replace("_", " "),
                      "per_payment": w.agent.per_txn_limit, "per_day": w.agent.daily_budget,
                      "approval_at": w.agent.approval_threshold},
            "payees": [m.name for m in w.merchants], "open_payees": w.open_payees,
            "payee_ids": {m.merchant_id: m.name for m in w.merchants},
            "policy_version": policy.version, "disabled_checks": sorted(policy.disabled_checks), "llm_checks": llm_checks,
            "aml_monitoring": aml}


@app.get("/api/levels")
def levels():
    vid = visitor()
    prog = {}
    kv = store.KV("llm:")
    for k in ORDER:
        att = store.attempts(vid[0], k)
        # Replays use cached model answers, so this makes no new LLM calls for levels already played.
        prog[k] = {"attempts": len(att), "won": bool(att) and run(WORLDS[k], att, llm=llm(), store=kv)["won"]}
    return respond({"levels": [world_info(WORLDS[k]) for k in ORDER], "progress": prog, "vault": store.vault(),
                    "tries_left": max(0, store.CAPS["visitor_attempts"] - store.used("visitor_attempts", vid[0]))}, vid)


@app.get("/api/level/<key>")
def level_state(key):
    if key not in WORLDS:
        return respond({"error": "unknown level"}, status=404)
    vid = visitor()
    att = store.attempts(vid[0], key)
    kv = store.KV("llm:")
    res = run(WORLDS[key], att, llm=llm(), store=kv) if att else None
    rv = reveal(WORLDS[key], att, llm=llm(), store=kv) if res and res["won"] else None
    return respond({"level": world_info(WORLDS[key]), "attempts": att, "result": res, "reveal": rv}, vid)


@app.post("/api/attempt")
def attempt():
    vid = visitor()
    body = request.get_json(force=True, silent=True) or {}
    key = body.get("level")
    if key not in WORLDS:
        return respond({"error": "unknown level"}, vid, 404)
    w = WORLDS[key]
    docs = {t: str((body.get("documents") or {}).get(t) or "")[:MAX_DOC] for t in w.tools}
    if not any(v.strip() for v in docs.values()):
        return respond({"error": "Write something for the agent to read first."}, vid, 400)
    client = llm()
    if client is None:
        return respond({"error": "The AI agent is offline right now (no model key configured)."}, vid, 503)
    capped = store.take([("visitor_attempts", vid[0], store.CAPS["visitor_attempts"]),
                         ("ip_attempts", store.ip_hash(client_ip()), store.CAPS["ip_attempts"]),
                         ("site_attempts", "all", store.CAPS["site_attempts"])])
    if capped:
        msg = ("You've used today's tries. Come back tomorrow, or read how AgentGuard was evaluated in For professionals."
               if capped != "site_attempts" else "The game has hit today's site-wide limit. Please come back tomorrow.")
        return respond({"error": msg, "capped": capped}, vid, 429)
    kv = store.KV("llm:")
    prior = store.attempts(vid[0], key)
    try:
        props, note, _ = propose(client, w, docs, store=kv)
    except AgentUnavailable:
        return respond({"error": "The AI agent could not be reached. Please try again in a moment."}, vid, 503)
    a = {"n": len(prior), "documents": docs, "proposals": [p.as_dict() for p in props], "note": note}
    res = run(w, prior + [a], llm=client, store=kv)
    last = res["attempts"][-1]["rows"]
    prot = sum(r["waste"] for r in last if not r["settled"])
    lost = sum(r["waste"] for r in last if r["settled"])
    store.add_attempt(vid[0], key, a)
    store.vault_add(prot, lost, caught=prot > 0)
    rv = reveal(w, prior + [a], llm=client, store=kv) if res["won"] else None
    return respond({"attempt": a, "result": res, "reveal": rv, "vault": store.vault(),
                    "tries_left": max(0, store.CAPS["visitor_attempts"] - store.used("visitor_attempts", vid[0]))}, vid)


@app.post("/api/reset")
def reset():
    vid = visitor()
    key = (request.get_json(force=True, silent=True) or {}).get("level")
    if key in WORLDS:
        store.reset_level(vid[0], key)
    return respond({"ok": True}, vid)


@app.post("/api/donate")
def donate():
    vid = visitor()
    body = request.get_json(force=True, silent=True) or {}
    key = body.get("level")
    if key not in WORLDS or body.get("consent") is not True:
        return respond({"error": "Consent is required."}, vid, 400)
    att = store.attempts(vid[0], key)
    if not att:
        return respond({"error": "Nothing to donate."}, vid, 400)
    res = run(WORLDS[key], att, llm=llm(), store=store.KV("llm:"))
    if not res["won"]:
        return respond({"error": "Only winning attacks can be donated."}, vid, 400)
    if store.take([("visitor_donations", vid[0], store.CAPS["visitor_donations"])]):
        return respond({"error": "You've donated 3 attacks today. Thank you!"}, vid, 429)
    a = att[-1]
    sid, problem = store.donate(key, res["policy_version"], a["documents"], a["proposals"], "won")
    if problem:
        return respond({"error": problem + " Nothing was stored."}, vid, 400)
    return respond({"submission_id": sid}, vid)


@app.post("/api/donate/delete")
def donate_delete():
    sid = str((request.get_json(force=True, silent=True) or {}).get("submission_id") or "")
    return respond({"deleted": store.delete_donation(sid)})


# -- Analyst shift ---------------------------------------------------------------------

def shift_seed() -> int:
    s = request.args.get("seed") or (request.get_json(force=True, silent=True) or {}).get("seed") or "daily"
    if s == "daily":
        return int(store.today().replace("-", ""))
    try:
        return max(1, min(int(s), 10**9))
    except ValueError:
        return 1


def cents(text: str) -> str:
    """Round code-written dollar amounts to cents for display (synthetic data has sub-cent amounts)."""
    import re
    return re.sub(r"\$(\d[\d,]*)\.(\d{2})(\d+)", lambda m: fmt_usd(int(round(float(m.group(1).replace(",", "") + "." + m.group(2) + m.group(3)) * 100)) * 10_000), text)


def subject_name(sh, a) -> str:
    if a.subject_type == "merchant":
        m = sh.registry.merchants.get(a.subject_id)
        return m.name if m else a.subject_id
    return a.subject_id if a.subject_type == "agent" else f"team {a.subject_id}"


def alert_row(sh, a):
    total = sum(sh.by_id[t].amount for t in a.txn_ids)
    return {"id": a.alert_id, "rule": str(a.rule).replace("AML_", "").replace("_", " ").lower(), "code": str(a.rule),
            "severity": a.severity, "subject": subject_name(sh, a), "total": total, "payments": len(a.txn_ids),
            "raised_at": a.raised_at.isoformat(), "explanation": cents(a.explanation)}


@app.get("/api/shift")
def shift():
    seed = shift_seed()
    sh = generate(seed)
    return respond({"seed": seed, "budget": SHIFT_BUDGET, "seconds": SHIFT_SECONDS,
                    "alerts": [alert_row(sh, a) for a in sh.alerts]})


@app.post("/api/shift/open")
def shift_open():
    vid = visitor()
    body = request.get_json(force=True, silent=True) or {}
    sh = generate(shift_seed())
    a = next((x for x in sh.alerts if x.alert_id == body.get("alert_id")), None)
    if a is None:
        return respond({"error": "unknown alert"}, vid, 404)
    rows = []
    for t in [sh.by_id[i] for i in a.txn_ids][:25]:
        m = sh.registry.merchants[t.merchant_id]
        rows.append({"id": t.txn_id, "at": t.timestamp.isoformat(), "agent": t.agent_id, "merchant": m.name,
                     "category": m.category, "trusted": m.trusted, "amount": t.amount})
    hist = None
    if a.subject_type == "agent":
        hist = [t for t in sh.txns if t.agent_id == a.subject_id and t.timestamp < a.raised_at - timedelta(hours=1)][-60:]
    note = None
    client = llm()
    if client is not None and not store.take([("visitor_notes", vid[0], store.CAPS["visitor_notes"]),
                                              ("site_notes", "all", store.CAPS["site_notes"])]):
        n = Investigator(client, model=CHECK_MODEL, store=store.KV("inv:"), max_retries=2).draft(a, sh.by_id, sh.registry, hist)
        note = n.as_dict()
    return respond({"alert": alert_row(sh, a), "transactions": rows, "case_note": note,
                    "usual_merchants": sorted({sh.registry.merchants[t.merchant_id].name for t in (hist or [])})[:6]}, vid)


@app.post("/api/shift/score")
def shift_score():
    body = request.get_json(force=True, silent=True) or {}
    sh = generate(shift_seed())
    ids = {a.alert_id for a in sh.alerts}
    opened = [x for x in (body.get("opened") or []) if x in ids][:SHIFT_BUDGET]
    escalated = [x for x in (body.get("escalated") or []) if x in opened]
    you, eng, top = score(sh, escalated), score(sh, ranked(sh)[:SHIFT_BUDGET]), score(sh, best(sh, SHIFT_BUDGET))
    truth = {a.alert_id: sh.alert_truth(a) for a in sh.alerts}
    return respond({"you": you, "engine_ranked": eng, "best": top, "truth": truth, "engine_order": ranked(sh)[:SHIFT_BUDGET],
                    "penalty_note": "ASSUMPTION: a false alarm costs $50.00 of analyst time (simulated)."})


@app.get("/api/vault")
def vault():
    return respond(store.vault())


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5200)), debug=False)
