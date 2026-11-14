# Stage 4 design (current)

**Source of truth:** [GAME_DESIGN.md](GAME_DESIGN.md) (from Nakul). Earlier designs are archived in `v1-dashboard/` and `v2-vault/`.

| File | What it is |
|---|---|
| `wireframes.html` | Low-fidelity wireframes, desktop and phone: home, level play, the three verdicts, win reveal + consent, Level 4 with gaps, boss, Analyst shift (dark), For professionals |
| `swatches.html` | Colour swatches (light and dark), stamp verdicts, type scale, WCAG contrast ratios |
| `level1.html` | One fully designed screen: Level 1 with a HELD stamp. Its verdict, reason code, decision ID and audit hash are real engine output (`tools/level1_sample.py`) |
| `tools/contrast.py` | Computes every contrast ratio shown (writes `tools/contrast.json`) |

## Each level against the engine

| Level | Defence in GAME_DESIGN.md | Engine today | Work before it can ship |
|---|---|---|---|
| 1 Accounts-payable agent | Four-eyes approval from the system, never from text | `human_approval` with signed, payment-bound approvals; approver ≠ owner | None |
| 2 Pay-per-call drain | Velocity + cumulative per-merchant checks | `agent_velocity`, `merchant_daily_limit`, `split_check` | The split check ignores payments under 10% of the approval threshold, so micropayments are caught only by the per-merchant daily cap and velocity limit. The level will set a per-API daily cap. I'll say this on screen. |
| 3 Travel agent | Look-alike detection + trusted registry | `lookalike_merchant` (edit distance, homoglyphs), registry | An "open payee" switch so the agent may try a new payee (added after lock) |
| 4 Free-trial trap | Recurring-commitment and stored-credential holds | **Built in this round, added after lock:** `recurring_commitment`, `stored_credential` (`agentguard/commitments.py`, 8 tests) | None. Remaining gaps are listed on the Level 4 screen |
| 5 Intent mismatch | Injection check + **intent check against the original request** | Injection check is built. **The intent check is not built.** | Build an intent check: code compares the proposed purchase (merchant category, item, amount) with the person's original request; the LLM may flag a mismatch with reasons; code decides |
| Boss | Everything, adaptive | All of the above, AML monitoring with AML→hold | Per-level switches for checks that are always on today (look-alike, velocity), so early levels genuinely lack later defences |

**Analyst shift** needs a seeded synthetic data generator (agent transactions with planted patterns, including IBM-style fan-in, scatter-gather and cycles). GAME_DESIGN.md also asks for the AI investigator's case note on each opened alert, so the investigator and its E3 citation check must be built before this mode ships.

## Level 4 gaps that stay (shown on screen)
- After approval, later charges on a stored card don't pass through AgentGuard unless the payment rail routes them here.
- No subscription ledger: renewals and cancellations aren't tracked after sign-up (future liabilities are recorded at sign-up only).
- Terms are found by English keyword patterns; terms in images, PDFs or reworded text can be missed.
- No worst-case amount when the terms give no price or period; auto top-up has no upper limit.

## Colour finding that needs a decision
Held amber `#B7791F` is 3.23:1 on paper, so it fails WCAG AA for small text (it passes for the large stamp). Proposal: keep it exactly for stamps, borders and icons; add `--held-ink #8F5E15` (4.93:1 on paper) for small HELD labels and reason codes; use ink, not white, on amber fills. The hairline `#E3DED3` (1.34:1) stays decorative; form controls get a `#5B6270` border (6.13:1).
