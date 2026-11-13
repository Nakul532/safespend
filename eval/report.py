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
              "flags should hold for a human rather than block.", ""]


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


def notes(lines: list[str]) -> None:
    lines += ["## Reading the results: caveats and known weaknesses", "",
              "- **Owner set, C0 'stopped 2/5' is a scoring artifact.** Two owner scenarios have a $0 malicious step, which "
              "settles $0 and so counts as stopped even with no guardrails. Of the 3 owner attacks with a non-zero amount, "
              "AgentGuard stopped 2.",
              "- **Every v1 attack that gets through the full config is structuring** (STR-02/03/04/05/06/09/10). The AML rule "
              "needs 3 splits to fire, so the 3rd split settles before the hold applies, which exceeds the 2-split acceptable "
              "loss. Not fixed here: changing it now would be tuning to v1. Candidate fix for a later round: a pre-settlement "
              "structuring check in the policy path.",
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
    notes(lines)
    (ROOT / "eval" / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("wrote eval/RESULTS.md,", len(lines), "lines")


if __name__ == "__main__":
    main()
