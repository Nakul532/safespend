"""Builds eval/RESULTS.md from eval/results/*.json."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "redteam" / "runner"))
import redteam as rt  # noqa: E402

R = ROOT / "eval" / "results"
MAIN = ["C0 no guardrails", "C1 policy (as locked)", "C1+ policy + price check + fuzzy sanctions",
        "C2 policy + injection check", "C3- full, AML flags only", "C3 full, AML->hold sev 7"]
SHORT = {"C0 no guardrails": "C0 none", "C1 policy (as locked)": "C1 policy (locked)",
         "C1+ policy + price check + fuzzy sanctions": "C1+ policy +price +fuzzy†",
         "C2 policy + injection check": "C2 +injection†", "C3- full, AML flags only": "C3− +AML flags",
         "C3 full, AML->hold sev 7": "C3 full (AML→hold 7)†"}


def money(s: str) -> str:
    return f"${Decimal(s):,.2f}"


def e1(lines: list[str]) -> None:
    s = json.loads((R / "e1" / "summary.json").read_text())
    lines += ["## E1: red-team results", "",
              "**Configs.** C0: no guardrails. C1: Stage 1 policy engine exactly as locked (exact-match sanctions, no price check). "
              "C1+: C1 plus the quoted-vs-charged price check and fuzzy sanctions screening. C2: C1+ plus the injection check. "
              "C3−: C2 plus AML monitoring that only flags. C3: C2 plus AML monitoring with AML→hold at severity 7. "
              "† = includes something **added after lock**; C1 is the before, the † columns are the after.", "",
              "All money is SIMULATED. Configs with the LLM ran 3 times (temperature 0); results were identical across "
              "the 3 runs for every set (see the variation table), so run 1 is shown.", ""]
    for key, label in s["sets"].items():
        cols = {SHORT[c]: s["results"][key][c]["run1"] for c in MAIN}
        held = key != "v1"
        lines += [f"### {label}", ""]
        if held:
            lines += ["Held-out: aggregate results only; per-scenario results were not saved or read.", ""]
        md = rt.render_markdown(cols).split("\n")
        lines += [ln.replace("### ", "#### ") for ln in md[2:]]
    # Variation and sensitivity
    lines += ["### Variation across the 3 LLM runs", "", "| Set | Config | Attacks stopped (min–max) | False blocks (min–max) | Dollars lost (min–max) |", "|---|---|---|---|---|"]
    for key, label in s["sets"].items():
        for c in ("C2 policy + injection check", "C3 full, AML->hold sev 7"):
            runs = s["results"][key][c]
            st = [r["overall"]["attacks_stopped"] for r in runs.values()]
            fb = [r["overall"]["false_blocks"] for r in runs.values()]
            dl = [Decimal(r["overall"]["dollars_lost_usd"]) for r in runs.values()]
            lines.append(f"| {label} | {SHORT[c]} | {min(st)}–{max(st)} | {min(fb)}–{max(fb)} | {money(min(dl))}–{money(max(dl))} |")
    lines += ["", "### AML→hold sensitivity (added after lock)", "",
              "| Set | Severity threshold | Attacks stopped | Dollars lost | Held for a human | False blocks |", "|---|---|---|---|---|---|"]
    for key, label in s["sets"].items():
        for sev, c in ((None, "C3- full, AML flags only"), (5, "C3 sens, AML->hold sev 5"), (7, "C3 full, AML->hold sev 7"), (9, "C3 sens, AML->hold sev 9")):
            o = s["results"][key][c]["run1"]["overall"]
            lines.append(f"| {label} | {sev or 'off (flags only)'} | {o['attacks_stopped']}/{o['attacks']} | {money(o['dollars_lost_usd'])} | "
                         f"{o['held_for_human_pct']}% | {o['false_blocks']}/{o['legitimate']} |")
    lat = s["latency"]
    lines += ["", "### Latency (measured on a laptop; SIMULATED payments)", "",
              "| Path | n | p50 | p95 |", "|---|---|---|---|",
              f"| Deterministic policy path (no LLM) | {lat['deterministic_path_ms']['n']} | {lat['deterministic_path_ms']['p50']} ms | {lat['deterministic_path_ms']['p95']} ms |",
              f"| LLM call (Groq API, gpt-oss-120b) | {lat['llm_path_ms_end_to_end']['n_live_calls']} | {lat['llm_api_ms']['p50']:.0f} ms | {lat['llm_api_ms']['p95']:.0f} ms |",
              f"| LLM path as measured by the eval harness | {lat['llm_path_ms_end_to_end']['n_live_calls']} | {lat['llm_path_ms_end_to_end']['p50']:.0f} ms | {lat['llm_path_ms_end_to_end']['p95']:.0f} ms |",
              "", f"Share of payments that needed the LLM: **{lat['share_needing_llm']['llm_steps']} of {lat['share_needing_llm']['all_steps']} "
              f"({lat['share_needing_llm']['pct']}%)**, across all four sets, which are heavy in injection scenarios. "
              "The deterministic path is well under the 100 ms p95 target. "
              "The harness figure includes a 2.5 s pause between calls to stay under Groq's free-tier rate limit; "
              "it is test overhead, not AgentGuard. A real authorization on the LLM path costs the deterministic time plus the API call.", ""]


def capabilities(lines: list[str]) -> None:
    c = json.loads((R / "capability_counts.json").read_text())
    names = {"heldout-model-v1": "Model-written (18)", "heldout-external-v1": "External (6)", "heldout-owner-v1": "Owner incidents (5)"}
    lines += ["## Held-out scenarios that depend on unbuilt capabilities", "",
              "Counted from each scenario's `missing_capabilities` tags by keyword, without reading scenario content. "
              "Tags phrased differently may be missed, so these are lower bounds.", "",
              "| Set | Scenarios | Any missing capability | Recurring charges | Stored credentials | Future liabilities | Any of these three |",
              "|---|---|---|---|---|---|---|"]
    for k, v in c.items():
        lines.append(f"| {names[k]} | {v['scenarios']} | {v['with_any_missing_capability']} | {v['recurring_charges']} | "
                     f"{v['stored_credentials']} | {v['future_liabilities']} | {v['any_of_the_three']} |")
    lines.append("")


def lookalike(lines: list[str]) -> None:
    p = R / "lookalike_fp.json"
    if not p.exists():
        return
    d = json.loads(p.read_text())
    a, b = d["test_a_vs_world_merchants"], d["test_b_vs_top_registrants"]
    lines += ["## Look-alike false positives on real company names", "",
              f"Source: SEC `company_tickers.json` (public), {d['distinct_companies']:,} distinct registrants. "
              "Every pair is two different real companies, so every flag is a false positive. "
              "The look-alike check is unchanged from Stage 1.", "",
              "| Test | Trusted list | Names checked | Flagged | Rate |", "|---|---|---|---|---|",
              f"| A: against the suite's 9 fictional merchants | 9 | {a['checked']:,} | {a['flagged']} | {a['pct']}% |",
              f"| B: against the 500 largest SEC registrants | {b['trusted_list_size']} | {b['checked']:,} | {b['flagged']} | {b['pct']}% |",
              "", f"Test B by reason: {b['by_reason']['edit_distance_only']} by edit distance alone, "
              f"{b['by_reason']['contains_trusted_name']} because the name contains a trusted name.", "",
              "Examples (flagged name → trusted name it was matched to):", ""]
    for e in a["examples"]:
        lines.append(f"- A: {e[0]} → {e[1]} (distance {e[2]})")
    for e in b["examples"][:15]:
        lines.append(f"- B: {e[0]} → {e[1]} ({'contains the name' if e[3] else f'distance {e[2]}'})")
    lines += ["", "**Reading:** short names (three to five letters after normalisation) produce most edit-distance flags, "
              "and corporate families (Cheniere Energy Partners → Cheniere Energy) produce the 'contains' flags. "
              "With a short, curated trusted list the rate is low; with hundreds of trusted brands it is high enough that "
              "flags should hold for a human rather than block.", "",
              "**Round 2 change (added after Stage 3 results):** with `lookalike_hold_min_trusted=50`, a look-alike match "
              "against a trusted list of 50 or more merchants now holds the payment for a human (LOOKALIKE_REVIEW) instead of "
              "blocking it. With fewer trusted merchants, as in the suite's world of 9, it still blocks. On Test B the 249 "
              "flags would all be holds, so 0 legitimate companies would be blocked by this check.", ""]


def e2(lines: list[str]) -> None:
    p = R / "e2_ibm.json"
    if not p.exists():
        lines += ["## E2: IBM AML benchmark", "", "Not run yet.", ""]
        return
    d = json.loads(p.read_text())
    u = d["unbudgeted"]
    lines += ["## E2: IBM AML benchmark (synthetic public benchmark)", "",
              f"{d['benchmark']}, {d['subset']}: {d['transactions']:,} transactions, {d['laundering']:,} labelled laundering. "
              f"{d['settings_note']}. {d['fx_note']}. Runtime {d['runtime_seconds']} s.", "",
              "The rules were written for AI agents paying merchants; here they run on bank transfers with "
              "bank-scale settings. The baseline flags every transfer of $10,000 or more.", "",
              "### All alerts (no budget)", "",
              "| Detector | Alerts | Flagged txns | Precision | Recall | False-positive rate | Alert-to-case rate |", "|---|---|---|---|---|---|---|"]
    a = u["all_rules"]
    lines.append(f"| All AgentGuard rules | {a['alerts']:,} | {a['flagged']:,} | {a['precision']} | {a['recall']} | {a['fpr']} | {a['alert_to_case']} |")
    for name, v in u["per_rule"].items():
        lines.append(f"| · {name} | {v['alerts']:,} | {v['flagged']:,} | {v['precision']} | {v['recall']} | {v['fpr']} | {v['alert_to_case']} |")
    b = u["baseline_amount_>=_10000"]
    lines += [f"| Baseline: amount ≥ $10,000 | {b['flagged']:,} | {b['flagged']:,} | {b['precision']} | {b['recall']} | {b['fpr']} | {b['precision']} |", "",
              "### At a daily alert budget (analysts review K alerts a day)", "",
              "| K per day | Rules: precision | Rules: recall | Rules: alert precision | Baseline: precision | Baseline: recall |", "|---|---|---|---|---|---|"]
    for k, v in d["daily_alert_budgets"].items():
        r, bb = v["rules"], v["baseline_top_amounts"]
        lines.append(f"| {k.split('/')[0][2:]} | {r['precision']} | {r['recall']} | {r['alert_precision']} | {bb['precision']} | {bb['recall']} |")
    lines += ["", "Rule alerts can cover many transactions, so 'alert precision' (share of reviewed alerts containing any "
              "laundering) is shown next to transaction-level precision. The baseline reviews the K largest transfers each day.", "",
              "### Recall by laundering pattern", "", "| Pattern | Laundering txns | Rules recall | Baseline recall |", "|---|---|---|---|"]
    for pat, v in d["recall_by_pattern"].items():
        lines.append(f"| {pat} | {v['laundering_txns']:,} | {v['rules_recall']} | {v['baseline_recall']} |")
    lines.append("")


def round2(lines: list[str]) -> None:
    p = R / "e1" / "round2.json"
    if not p.exists():
        return
    r2 = json.loads(p.read_text())
    s = json.loads((R / "e1" / "summary.json").read_text())
    lines += ["## Round 2: pre-payment split check (added after Stage 3 results)", "",
              "Before a payment settles, AgentGuard adds it to the same merchant's payments from the last 24 hours, for the "
              "agent and for every agent with the same owner, and holds it for a human once the total reaches the agent's "
              "approval threshold. Payments under 10% of the threshold are ignored, so micropayments do not trip it. "
              "Settings were fixed and frozen (tag `eval-freeze-2`) before any held-out set was run; each held-out set ran once. "
              "The look-alike review hold (below) was switched on in these configs too; with 9 trusted merchants it never applies.", "",
              "**The v1 suite is not a clean test of this check:** the builder saw the v1 structuring failures that motivated it. "
              "Judge it on the held-out sets. The held-out sets contain no legitimate tasks, so false blocks can only be "
              "measured on v1.", "",
              "| Set | Config | Attacks stopped | Dollars lost | False blocks | Held for a human | Adaptive stopped |", "|---|---|---|---|---|---|---|"]
    pairs = (("C1+ (before)", lambda k: s["results"][k]["C1+ policy + price check + fuzzy sanctions"]["run1"]),
             ("C1+ + split check", lambda k: r2["results"][k]["C1+S policy + price + fuzzy + split check"]),
             ("C3 full (before)", lambda k: s["results"][k]["C3 full, AML->hold sev 7"]["run1"]),
             ("C4 full + split check", lambda k: r2["results"][k]["C4 full + split check"]))
    order = ["heldout-model", "heldout-external", "heldout-owner", "v1"]
    for k in order:
        for name, get in pairs:
            x = get(k); o, a = x["overall"], x["adaptive_attacks"]
            ad = f"{a['attacks_stopped']}/{a['attacks']}" if a["attacks"] else "none in set"
            fb = f"{o['false_blocks']}/{o['legitimate']}" if o["legitimate"] else "n/a (no legitimate tasks)"
            lab = s["sets"][k] + (" (not clean)" if k == "v1" else "")
            lines.append(f"| {lab} | {name} | {o['attacks_stopped']}/{o['attacks']} | {money(o['dollars_lost_usd'])} | {fb} | {o['held_for_human_pct']}% | {ad} |")
    lines += ["", "LLM answers in C4 came from the run1 cache (identical inputs, temperature 0; the three Stage 3 runs matched), so C4 ran once.", ""]


def rapidfire(lines: list[str]) -> None:
    p = R / "e2_rapidfire.json"
    if not p.exists():
        lines += ["## Round 2: rapid-fire retune on IBM", "", "Not run yet.", ""]
        return
    d = json.loads(p.read_text())
    c, old = d["chosen"], d["stage3_setting"]
    lines += ["## Round 2: rapid-fire retune on IBM HI-Small (added after Stage 3 results)", "",
              f"Tuned on days 1–3 ({d['train']['transactions']:,} transactions, {d['train']['laundering']:,} laundering), "
              f"tested once on days 4–7 ({d['test']['transactions']:,} transactions, {d['test']['laundering']:,} laundering). "
              "Grid and objective were committed before running: window × minimum count, maximise the rule's "
              "transaction-level F1 on days 1–3. Caveat: the Stage 3 report already showed 7-day totals that include days 4–7.", "",
              f"Stage 3 setting: {old['min_count']}+ transfers within {old['window_s']} s. "
              f"Chosen: **{c['min_count']}+ within {c['window_s']} s** (days 1–3: precision {c['precision']}, recall {c['recall']}, F1 {c['f1']}, {c['alerts']:,} alerts).", "",
              "### Days 4–7 (test), before and after", "",
              "| Detector | Alerts | Flagged txns | Precision | Recall | False-positive rate | Alert-to-case |", "|---|---|---|---|---|---|---|"]
    for name, key in (("Before: all rules", "test_before"), ("After: all rules (tuned rapid-fire)", "test_after")):
        a = d[key]["unbudgeted"]["all_rules"]
        lines.append(f"| {name} | {a['alerts']:,} | {a['flagged']:,} | {a['precision']} | {a['recall']} | {a['fpr']} | {a['alert_to_case']} |")
        rf = d[key]["unbudgeted"]["per_rule"]["rapid_fire"]
        lines.append(f"| · rapid-fire alone | {rf['alerts']:,} | {rf['flagged']:,} | {rf['precision']} | {rf['recall']} | {rf['fpr']} | {rf['alert_to_case']} |")
    b = d["test_before"]["unbudgeted"]["baseline_amount_>=_10000"]
    lines += [f"| Baseline: amount ≥ $10,000 | {b['flagged']:,} | {b['flagged']:,} | {b['precision']} | {b['recall']} | {b['fpr']} | {b['precision']} |", "",
              "| K per day | Before: recall | Before: alert precision | After: recall | After: alert precision | Baseline: recall |", "|---|---|---|---|---|---|"]
    for k in d["test_before"]["daily_alert_budgets"]:
        bb, aa = d["test_before"]["daily_alert_budgets"][k], d["test_after"]["daily_alert_budgets"][k]
        lines.append(f"| {k.split('/')[0][2:]} | {bb['rules']['recall']} | {bb['rules']['alert_precision']} | {aa['rules']['recall']} | "
                     f"{aa['rules']['alert_precision']} | {bb['baseline_top_amounts']['recall']} |")
    lines += ["", "**Reading:** the retune cuts alerts on days 4–7 by about four-fifths and halves the false-positive rate, and "
              "alert-to-case rises from 0.7% to 2.9%; recall falls from 33% to 27%. Under a daily budget nothing changes up to "
              "K=100, because rapid-fire alerts (severity 5) rank below the other rules' alerts. The tuned rule's 28 alerts "
              "each cover thousands of transfers from very busy accounts, which an analyst cannot review as one case: "
              "rapid-fire suits agents better than bank accounts.", "", "<details><summary>Full tuning grid (days 1–3)</summary>", "", "| Window | Min count | Alerts | Precision | Recall | F1 |", "|---|---|---|---|---|---|"]
    for g in d["grid_on_train"]:
        lines.append(f"| {g['window_s']} s | {g['min_count']} | {g['alerts']:,} | {g['precision']} | {g['recall']} | {g['f1']} |")
    lines += ["", "</details>", ""]


def notes(lines: list[str]) -> None:
    lines += ["## Reading the results: caveats and known weaknesses", "",
              "- **Owner set, C0 'stopped 2/5' is a scoring artifact.** Two owner scenarios have a $0 malicious step, which "
              "settles $0 and so counts as stopped even with no guardrails. Of the 3 owner attacks with a non-zero amount, "
              "AgentGuard stopped 2.",
              "- **Every v1 attack that gets through the full config is structuring** (STR-02/03/04/05/06/09/10). The AML rule "
              "needs 3 splits to fire, so the 3rd split settles before the hold applies, which exceeds the 2-split acceptable "
              "loss. Round 2 adds a pre-payment split check for this; it is judged on the held-out sets because v1 "
              "motivated it.",
              "- **LEG-INJ-06** (legitimate) is held for a human under the injection check: a friction hold, not a false block.",
              "- **Latency:** the harness LLM-path figure includes a 2.5 s rate-limit pause; the API figure is the real cost.",
              "- **LLM provider:** Groq called directly (no OpenRouter key). Same model as planned.",
              "- **E2, read plainly:** with every alert counted, the rules are no more precise than the $10,000 threshold "
              "(0.15% vs 0.13%) and flag about as many transactions. rapid_fire produces most of the noise; fan_in is the only "
              "rule with useful signal (alert-to-case 4.9%, recall 62% on FAN-IN patterns). Under a daily review budget the "
              "rules find more laundering than the threshold from K=50 up (recall 3.1% vs 0.3% at K=50), and about 1 in 4–10 "
              "reviewed alerts contains laundering. The rules miss chain patterns (STACK, CYCLE, BIPARTITE) that need graph analysis.",
              "- **Limitations:** money is SIMULATED; the IBM data is synthetic; the suites are small (110 + 18 + 6 + 5); the "
              "injection dev set (30 items) was written by the builder; held-out sets were written by models of the same or "
              "different families, and the owner set was drafted with Claude, so none is fully independent.", ""]


def main() -> None:
    lines = ["# AgentGuard Stage 3 results", "",
             "Code frozen at tag `eval-freeze-1` before any locked set was run. Everything marked **added after lock** "
             "was built after the red-team suites were locked and is shown with and without it. "
             "LLM: gpt-oss-120b on Groq (planned OpenRouter pinned to Groq; no OpenRouter key was available, so Groq was called directly). "
             "Number sources: E1 = SIMULATED money, MEASURED results; E2 = BENCHMARK (IBM AML HI-Small, synthetic).", ""]
    e1(lines)
    capabilities(lines)
    lookalike(lines)
    e2(lines)
    round2(lines)
    rapidfire(lines)
    notes(lines)
    (ROOT / "eval" / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("wrote eval/RESULTS.md,", len(lines), "lines")


if __name__ == "__main__":
    main()
