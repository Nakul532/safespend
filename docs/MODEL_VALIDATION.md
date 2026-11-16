# Model validation report (SR 11-7 style)

SafeSpend is a portfolio project. Money is simulated; this report follows the structure of US bank model-risk guidance (Federal Reserve SR 11-7) to show how the controls would be validated, not to claim regulatory approval.

## 1. Purpose and scope
SafeSpend decides whether an AI agent may make a payment, and monitors settled payments for laundering patterns. Components in scope:
- **Deterministic policy engine** (`safespend/policy.py`): limits, budgets, allowlists, four-eyes approval, duplicates, velocity, split check, commitment holds. It makes every decision.
- **LLM checks** (gpt-oss-120b): the injection check and the intent check. They can only flag a payment for a human; code decides. If the model is unreachable, the payment is held.
- **AML monitoring** (`safespend/aml/rules.py`): ten rules over the ledger; alerts at or above severity 7 hold the agent.
- **AI investigator**: drafts case notes; code verifies every citation and removes model-written numbers.

Out of scope: real payment rails, real customer data, card networks, and charges made outside SafeSpend (for example on a stored card).

## 2. Limits of use
- Thresholds were set for the fictional worlds in the red-team suite and the game; a deployment must set its own.
- The LLM checks are English-only in testing.
- AML rules were written for agents paying merchants. On bank transfers (IBM benchmark) they work through a shim and lose precision.

## 3. Conceptual soundness
- **The LLM proposes, code decides.** No model output can approve a payment. `validate_payment()` is the only path to a signed settlement permit; the ledger refuses anything without one.
- **Approvals** are signed by the system, bound to the payment hash, expire, and cannot come from the agent's owner (segregation of duties).
- **Audit trail**: every decision is hash-chained to the previous record; `verify()` detects edits.
- **Fail closed**: an unreachable or unparseable model holds the payment.
- **Ledger**: double-entry; property-based tests show balances reconcile and never go negative.

## 4. Data
- Red-team suite v1: 55 attacks and 55 legitimate tasks, locked before any run.
- Held-out sets, locked and never used for development: model-written (18 attacks), external model (6), owner-sourced incidents (5, drafted with Claude). They contain no legitimate tasks, so false blocks are measured on v1 only.
- Intent-mismatch set: 26 cases (16 mismatch, 10 match), written by a fresh agent, locked before the intent check existed.
- IBM AML HI-Small (synthetic, CDLA-Sharing-1.0), first 7 days: 3.73M transactions, 3,027 laundering.
- SEC company tickers (public) for look-alike false positives.
- Synthetic agent payments (seeded generator, synth-v2: whole-cent amounts, IDs in time order) for Analyst shift and E3. E3 v4 also runs one alert frozen from the pre-fix data as a reference case.

## 5. Outcomes analysis
See the results tabs. Headlines, all MEASURED:
- Held-out model-written set: 12/18 attacks stopped by the Stage 3 full configuration, 14/18 with the split check (C4 and C5).
- External held-out: 6/6. Owner incidents: 4/5 under C4, 5/5 under C5 (commitment holds).
- Legitimate tasks blocked: 0/55 in every configuration. Held for a human: 1/55 under C4, 6/55 under C5 (the commitment hold catches subscription renewals).
- Intent set: 26/26 correct in three runs (16/16 mismatches held, 10/10 matches allowed); fields alone catch 4/16.
- IBM, first 7 days, all alerts: precision 0.15% vs 0.13% for a $10,000 threshold. At 50 reviews a day: recall 3.1% vs 0.3%.
- E3 v4, shipped version (pack p4, prompt v4-p4, 31 alerts, synthetic data synth-v2): code writes each note's summary and the basis for its recommendation from the evidence pack; the model adds why it matters, open questions, actions and the recommendation label. 100% of cited evidence IDs exist; 197 of 248 model-written lines kept; 26 of 31 notes keep a why-it-matters sentence. Judge (qwen3.8-27b) on the 37 kept why-it-matters sentences: 84% supported, 3 partly, 3 unsupported, none arguing against the rule. Checklist on model-written lines only: next steps 100%, merchant concentration 87%, limit proximity 80%, cross-alert links 68%, time window 6% (code states timing). Known trade-off: the model recommended escalate for all 31 alerts, including all 14 benign ones; it never chose more_info or clear. Earlier E3 v4 versions, each changed after seeing results and run once: p2 (76% of 138 claim lines supported), p3 (71% of 133); v3: 90% of 30 kept sentences. Calls: 26 investigator calls direct to Groq, 6 retried after Groq rate limits via OpenRouter pinned to Groq (same model and settings, no fallbacks); recorded per call.
- E3 hand review of v3 notes, reported by source: owner hand-scored 1 note (1 line: supported, partly useful); AI-drafted verdicts approved by the owner, not human-verified, 9 notes (13 lines): 5 supported, 2 useful, 8 partly useful; recommendation agreed on 7 of 9.
- Latency: deterministic path p50 0.26 ms, p95 0.44 ms; LLM call p50 472 ms, p95 1,022 ms.

## 6. Sensitivity
- AML→hold at severity 5 and 7 give the same v1 result; at 9, losses rise from $1,169.80 to $1,567.35.
- Rapid-fire rule retuned on IBM days 1–3 and tested on days 4–7: alerts −79%, false-positive rate 0.21 → 0.09, recall 0.33 → 0.27; no change at budgets up to 100 a day.
- Look-alike check against a 500-name trusted list: 3.3% of real company names flagged; with 50 or more trusted names, matches hold instead of block.

## 7. Known weaknesses
- Structuring caught by AML only on the third split (fixed by the pre-payment split check, which ignores payments under 10% of the approval threshold).
- Small evaluation sets; perfect scores on 26 intent cases written by the builder's model family are not strong evidence.
- Commitment detection is keyword-based; stored-card charges outside SafeSpend are invisible; no subscription ledger.
- AML rules miss chain patterns (stack, cycle, bipartite) that need graph analysis.
- The investigator's claims are checked against the evidence pack, but the excuse filter is word-based and over-removes: it drops open questions such as "Is there a legitimate business need…?" and reasons such as "without an evident legitimate purpose". Half of v4 notes lose their summary, mostly to claim checks. The judge still finds 9 unsupported lines (for example "bulk of the payments" from a single merchant line).

## 8. Ongoing monitoring plan
- Re-run every locked set on each release; block release if any held-out result falls. Evals call models through OpenRouter pinned to Groq; the live site uses its own Groq key, so they never share a rate limit.
- Track hold rate, false-block rate, LLM error rate and latency daily; alert when the model fails closed more than 1% of calls.
- Visitor-submitted attacks (opt-in) become a new held-out set each quarter: locked, run once, reported in the adaptive subset.
- Review AML thresholds against alert-to-case rate monthly.
