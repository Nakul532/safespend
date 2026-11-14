"""Builds web/public/data/pro.json for the For professionals page from eval/results and docs/.
Run after any evaluation: python -m web.build_pro"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "eval" / "results"


def md(text: str) -> str:
    """Small Markdown subset: headings, paragraphs, lists, tables, bold, code."""
    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            n = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{min(n + 1, 4)}>{inline(ln[n:].strip())}</h{min(n + 1, 4)}>")
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|:]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[1:]
            out.append('<div class="tablewrap"><table class="t"><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table></div>")
            continue
        elif ln.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif ln.strip():
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "\n".join(out)


def main() -> None:
    s = json.loads((R / "e1/summary.json").read_text())
    r2 = json.loads((R / "e1/round2.json").read_text())
    c5 = json.loads((R / "e1/c5_boss.json").read_text())
    cfgs = [("C0 none", lambda k: s["results"][k]["C0 no guardrails"]["run1"]),
            ("C1 policy (locked)", lambda k: s["results"][k]["C1 policy (as locked)"]["run1"]),
            ("C2 + injection check", lambda k: s["results"][k]["C2 policy + injection check"]["run1"]),
            ("C3 + AML→hold", lambda k: s["results"][k]["C3 full, AML->hold sev 7"]["run1"]),
            ("C4 + split check", lambda k: r2["results"][k]["C4 full + split check"]),
            ("C5 boss: + commitment holds", lambda k: c5["results"][k]["C5 boss: C4 + commitment holds"])]
    order = [("heldout-model", "Held-out: model-written (18)"), ("heldout-external", "Held-out: external model (6)"),
             ("heldout-owner", "Held-out: owner incidents (5)"), ("v1", "Suite v1 (55 attacks, 55 legitimate; builder saw it)")]
    e1 = []
    for k, label in order:
        row = {"set": label, "cells": []}
        for name, get in cfgs:
            o = get(k)["overall"]
            row["cells"].append({"config": name, "stopped": o["attacks_stopped"], "attacks": o["attacks"], "lost": o["dollars_lost_usd"],
                                 "false_blocks": o["false_blocks"], "legit": o["legitimate"], "held_pct": o["held_for_human_pct"]})
        e1.append(row)
    e2 = json.loads((R / "e2_ibm.json").read_text())
    rf = json.loads((R / "e2_rapidfire.json").read_text())
    out = {
        "configs": [c for c, _ in cfgs], "e1": e1, "latency": s["latency"],
        "e2": {"subset": e2["subset"], "transactions": e2["transactions"], "laundering": e2["laundering"],
               "unbudgeted": {"rules": e2["unbudgeted"]["all_rules"], "baseline": e2["unbudgeted"]["baseline_amount_>=_10000"]},
               "budgets": e2["daily_alert_budgets"], "recall_by_pattern": e2["recall_by_pattern"]},
        "rapidfire": {"chosen": rf["chosen"], "before": rf["test_before"]["unbudgeted"]["all_rules"], "after": rf["test_after"]["unbudgeted"]["all_rules"]},
        "lookalike": json.loads((R / "lookalike_fp.json").read_text()),
        "intent": json.loads((R / "intent_locked.json").read_text())["runs"],
        "e3": json.loads((R / "e3.json").read_text()),
        "docs": {"validation": md((ROOT / "docs/MODEL_VALIDATION.md").read_text()),
                 "controls": md((ROOT / "docs/CONTROL_MATRIX.md").read_text())},
    }
    for x in out["lookalike"].values():
        if isinstance(x, dict):
            x["examples"] = x.get("examples", [])[:12]
    dest = ROOT / "web/public/data/pro.json"
    dest.write_text(json.dumps(out))
    print("wrote", dest, round(dest.stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
