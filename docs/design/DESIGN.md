# AgentGuard Stage 4 design v2: a game on a real engine (for approval, no UI code yet)

Replaces the dashboard-first design (kept in `v1-dashboard/`). Wireframes: `docs/design/wireframes.html`.
Level design: `docs/design/LEVELS.md`.

## The idea in one line
You play the attacker trying to trick an AI purchasing agent, or the analyst hunting laundering on a tight budget. Every outcome comes from the same engine the evals measured.

## Modes
| Mode | Who plays | Their goal | What it proves |
|---|---|---|---|
| **Break the bank** (main) | Any visitor | Get an AI purchasing agent to waste simulated money across five levels, each adding a defence | Each defence, live, against attacks we did not write |
| **Analyst shift** | Visitors, compliance people | Catch the most laundering with a limited review budget and a timer | Why alert ranking and alert budgets matter (the K-per-day metric from E2) |
| **For professionals** | Risk, compliance, hiring managers | Read the evidence | Dashboard, results, model validation report, control matrix |

## Credibility rules (apply to every screen)
1. **Real engine on every outcome.** Each attempt runs through `validate_payment()` with the level's config. The reason code, audit-log entry (with its real hash) and ledger balance on screen come from that run. No scripted outcomes.
2. **Two separate questions, shown separately.** (a) Did the AI agent take the bait? (b) Did AgentGuard stop the payment? The agent is deliberately naive (its prompt tells it to follow invoice instructions) and we say so, so the game tests AgentGuard, not the agent's caution. If the agent refuses on its own, it is shown as "the agent didn't bite", not as a win for AgentGuard.
3. **"Simulated money" strip** on every screen with money. Each number carries its source: SIMULATED (game), MEASURED (evals), BENCHMARK (IBM).
4. **Reveals are computed.** "Which defence would have stopped you" re-runs your exact payments through the next configs. If none would, we say so: that is a real gap, and the most valuable kind of submission.
5. **No digits from the LLM.** LLM-written reasons are shown only if they contain no digits; every number is from code.

## Personas and journeys

**Visitor-attacker** (main job: beat a level)
1. Lands on the home page; presses "Play: Break the bank".
2. Reads level 1's brief: the agent's task, its limits, the defences that are on.
3. Writes an attack in one of the attack tools (fake invoice, product page, look-alike merchant name, payment plan).
4. Presses "Send to the agent". Watches the pipeline: agent reads → agent proposes payment → each check runs → decision.
5a. Caught: the reason code stamps, the audit entry slides into the log, the vault counter rises. Tries again.
5b. Wins: sees the money wasted, then which later defence would have stopped them. Is asked once, opt-in, whether to donate the attack text to the visitor-submitted test set. Moves to the next level.

**Analyst** (main job: catch the most laundering in one shift)
1. Picks "Analyst shift"; reads the rules: 30 alerts, 8 reviews, 4 minutes (a relaxed mode has no timer).
2. Scans the queue (rule, severity, amount, agent) and picks an alert.
3. Opens it: facts computed by code and the transactions. Escalates or clears.
4. When the budget or time runs out, sees the score: laundering dollars caught, false escalations, what they missed, and how the engine's own ranking (severity, then amount) would have scored with the same budget.

**Professional** (main job: decide if it is credible)
1. Opens "For professionals" from any screen.
2. Reads the risk dashboard for the live game (attacks tried, stopped, money protected, which defences fired).
3. Opens results (E1/E2 tables and charts), the model validation report (SR 11-7 style), the control matrix (risk → control → test → evidence, OWASP LLM Top 10, FATF/FinCEN typologies).
4. Downloads the red-team suite or the audit log.

## Visitor-submitted held-out set (with explicit consent)
- **Consent:** after a winning attack, one dialog, a checkbox that starts unticked: "Donate this attack's text to AgentGuard's public test set (MIT licence). Don't include personal information." Declining changes nothing. Never asked for losing attempts, and never asked twice in a session for the same level.
- **What is stored:** attack text (capped at 2,000 characters per field), level, the config, the decision and reason code, the payments the agent proposed, a random submission ID shown to the visitor (for deletion requests), date. **Not stored:** IP address, name, email, account, device fingerprint. Rate limits use a salted hash of the IP that rotates daily and is never stored with the submission.
- **Moderation, in order:** (1) automatic personal-data scrub (emails, phone numbers, card-like numbers, IBANs, addresses) and rejection if anything remains; (2) an automatic content filter (slurs, sexual content, real people or brands named as targets); (3) human review before anything enters the set. Rejected items are deleted.
- **Caps:** 3 donations per visitor per day; 200 accepted per month; the set is closed and locked once it reaches 300 or at each quarterly lock, whichever comes first.
- **Held-out discipline:** donations go to a quarantine table. The builder never reads them for development. A fresh agent converts each batch to `SCHEMA.md`, it is locked in its own commit, and it runs once per config; aggregates only, as with the other held-out sets. Visitor attacks are **adaptive by nature**, so they are reported in the adaptive subset.
- **Public promise:** a short "What we keep" page, linked from the dialog.

## Analyst shift data
Synthetic agent transactions from a new seeded generator: normal agent purchasing plus planted patterns (structuring, split payments, rapid-fire, fan-in, look-alike merchants, dormant-then-active). The planted patterns are the labels. The alerts come from the real AML rules running on that data; nothing is hand-placed in the queue. Each shift is a fixed seed, so scores are comparable and a "daily shift" can be shared. IBM data is not used live (it is large and its licence would need attribution and share-alike on the site); E2 stays the benchmark.

## Accessibility and controls
- Every action has a button of at least 44 × 44 px and a keyboard shortcut (shown on the button): Enter to send, 1–4 to switch attack tools, J/K to move through alerts, E escalate, C clear, ? for help.
- Animations respect `prefers-reduced-motion` (stamps and vault become instant changes with the same text). Status always has a word and an icon as well as colour. The timer can be turned off (relaxed mode) and pauses when the tab is hidden.
- Phone: one column; the attack editor and the pipeline become two tabs; sticky bottom action bar.

## Visual direction
A game, but a credible one: the heist is the frame, the engine is the hero. Dark "vault" theme for the game (deep navy, brass accents for the vault, red/amber/green decisions), switching to the light finance-grade theme in "For professionals". Monospace for reason codes, hashes and money. Motion is short (under 600 ms) and tied to real events: a stamp when a check fails, a log entry when the audit log appends, coins into the vault when money is protected.

| Token | Value | Use |
|---|---|---|
| `--night` | #0B1220 | game background |
| `--panel` | #131C2E | game panels |
| `--text` | #E6EAF2 | game text (contrast 14:1 on `--night`) |
| `--muted` | #9AA4B8 | secondary text (7:1) |
| `--brass` | #D9A441 | vault, money protected, primary game button |
| `--allow` | #3CCB7F | ALLOW / money lost (on dark) |
| `--hold` | #F5B54A | HOLD |
| `--block` | #FF6B6B | BLOCK |
| Professionals | the v1 light tokens | dashboard, reports |

Type: Inter for text; JetBrains Mono for codes, hashes and money. Spacing 4/8/12/16/24/32/48.

## Build plan once approved
1. **Engine API** (Python serverless on Vercel): `POST /api/attempt` (level, attack fields) → agent LLM proposes payments → `validate_payment()` per payment → decision, reason code, audit entry, reveal. Game state per session in Turso. One engine change, behind a switch and labelled added after lock: an "open payee" policy (no allowlist) for levels 1–4, so the look-alike check has something to guard.
2. **Purchasing agent:** gpt-oss-20b on Groq, temperature 0, naive prompt, structured JSON output; code validates the JSON. Caps: 30 attempts per visitor per day, a site-wide daily cap, friendly limit message.
3. **Analyst shift generator + scoring** (deterministic, tested).
4. **UI** for the three modes, then the 3-task usability check on desktop and phone with screenshots.
5. **Donation pipeline** (scrub, filter, quarantine, review tool).
6. Professionals view: dashboard, results with charts, model validation report, control matrix.
7. Deploy, checklist on the live URL, README updates.

## Decisions I need from you
1. Approve the modes, levels (LEVELS.md) and wireframes, or say what to change.
2. **AI case notes** (the investigator, E3): show them inside Analyst shift as an optional "ask the investigator" hint that costs one review? That needs E3 done first. Or leave case notes for the professionals view only.
3. **Donation licence:** MIT (same as the suite) or CC0.
