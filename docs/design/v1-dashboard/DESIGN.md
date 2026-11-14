# AgentGuard Stage 4 design (for approval, no UI code yet)

Wireframes: open `docs/design/wireframes.html` in a browser (desktop and phone frames side by side, plus the token sheet).

## Personas and their one main job

| Persona | Who they are | One main job | Screen it lives on |
|---|---|---|---|
| Head of Risk | Owns losses and the risk committee report. Reads, rarely clicks. | "Is it safe to let our agents spend?" | Risk dashboard |
| Compliance analyst | Works alerts all day against a fixed review budget. | Clear the alert queue: decide each alert with evidence. | Alert queue + case note |
| Developer | Builds the agents or their guardrails. | Run the red-team against my agent and see what got through. | Red-team runner (and the sandbox) |

## User journeys

**Head of Risk: "is it safe?"**
1. Opens the risk dashboard from the landing page.
2. Reads the top row: losses prevented, residual loss, alert backlog, false-positive rate, circuit-breaker status, each with its source (SIMULATED / MEASURED / BENCHMARK).
3. Sees top typologies (structuring, injection, look-alike) and the one known weakness, with a link to the evidence.
4. Opens a typology to see the alerts behind it (goes to the analyst's queue, filtered).
5. Exports the audit log and checks "log verified" (the hash chain) for the committee pack.

**Compliance analyst: work the queue**
1. Opens the alert queue, sorted by severity then amount, with today's review budget shown ("12 of 50 reviewed").
2. Picks the top alert. The detail shows the rule, the facts computed by code and the transactions in a table.
3. Reads the AI case note. Every transaction ID it cites has a "checked against the ledger" mark; uncheckable notes are not shown.
4. Decides: escalate, close as false positive, or hold the agent. Adds a short reason (required).
5. Moves to the next alert; the backlog and budget counters update.

**Developer: run the red-team**
1. From the landing page, presses "Run the red-team" (replays from cache by default, so it costs nothing).
2. Picks the suite (v1, 110 scenarios) and the configuration (no guardrails … full).
3. Watches scenarios resolve live: allow / hold / block, with reason codes; category totals fill in.
4. Opens a scenario that got through and reads why.
5. Copies the command to run the same suite against their own guardrails (the MIT runner), or tries their own attack in the sandbox.

## Screens (wireframed desktop + phone)
1. **Landing:** one sentence on what it does; primary "Run the red-team"; secondary "Try to trick it" (sandbox); three MEASURED headline numbers; mock-money notice.
2. **Risk dashboard:** KPI row, top typologies, decisions over time, held-for-human queue, circuit breaker with resume control.
3. **Alert queue + case note:** list on the left, detail on the right (phone: list, then detail as its own screen).
4. **Red-team runner:** suite and config pickers, replay/live toggle, live results table, category bars.
5. **Injection sandbox:** write merchant-page text, set a payment, submit; see decision, reason code, heuristic hits and LLM reasons; cap counter.

Also planned (no separate wireframe; they reuse the layouts above): Results page, Track Record page, case study.

## Design tokens

**Colour (light).** Contrast checked against the background they sit on; every pair is at least 4.5:1 for text.

| Token | Value | Use |
|---|---|---|
| `--ink` | #0E1726 | body text, table text |
| `--ink-2` | #475467 | secondary text, labels |
| `--bg` | #F6F7F9 | page |
| `--surface` | #FFFFFF | cards, tables |
| `--line` | #D0D5DD | borders, table rules |
| `--primary` | #1849A9 | primary buttons, links |
| `--allow` | #067647 | ALLOW decisions |
| `--hold` | #93370D | HOLD (needs a human) |
| `--block` | #B42318 | BLOCK decisions |
| `--sim` | #5925DC | the SIMULATED / MEASURED / BENCHMARK source tags |

Status is never shown by colour alone: every status also has its word (ALLOW, HOLD, BLOCK) and an icon shape. A dark theme uses the same roles with lighter tints.

**Type.** Inter for interface text; JetBrains Mono with tabular figures for money, IDs, reason codes and hashes, so columns line up.

| Token | Size / line height | Use |
|---|---|---|
| `--t-xs` | 12 / 16 | table meta, source tags |
| `--t-sm` | 14 / 20 | tables (finance-grade density), labels |
| `--t-md` | 16 / 24 | body |
| `--t-lg` | 20 / 28 | section titles |
| `--t-xl` | 28 / 36 | KPI numbers, page titles |

**Spacing and shape.** 4-point scale: 4, 8, 12, 16, 24, 32, 48. Table rows 36 px on desktop (dense); tap targets at least 44 × 44 px everywhere, including on phones. Radius 6 px on cards and inputs, 8 px on buttons. One primary button per screen.

**Components that must not look default.** Data tables with sticky headers, right-aligned mono numbers and a source tag in the header. Decision pills (word + icon + colour). Source tags (SIMULATED / MEASURED / BENCHMARK) next to every number. A permanent "Mock money only" strip on every screen with money.

## Decisions I need from you
1. **AI case notes on the alert queue.** The investigator (E3) is not built yet. Option A: build it and run E3 inside Stage 4 before the alert queue ships (recommended; otherwise the queue has no case notes). Option B: ship the queue with facts only and mark case notes "next".
2. **Persistence:** Turso, as you noted, for ledger, audit log, idempotency store and approvals. The red-team replay reads cached results and needs no database.
3. **Live LLM on the site:** Groq gpt-oss-20b for the sandbox (cheaper, faster) with per-visitor and site-wide daily caps; 120b stays the eval model. Or 120b everywhere.
