# Build brief: SafeSpend, anti-money-laundering for AI agents

SafeSpend merges two of Nakul's projects (AgentPay and ComplianceGuard) into one product: a payment firewall for AI agents. Before a payment, guardrails decide whether an agent may spend. After payments, AML monitoring watches the stream of agent transactions for suspicious patterns, and an AI investigator writes evidence-cited case notes. Read DATA.md first: it lists the existing code and every fact you may reuse.

Owner: Nakul. Explain your plan before each stage and wait for his approval. He must understand every step.

## Who it's for
Teams letting AI agents pay for things (API calls, data, SaaS seats, procurement). Their fear: an agent gets tricked into spending money it shouldn't, or a pattern of small payments hides abuse.

## Core design rule: the LLM proposes, code decides
- Agents (LLM) propose purchases. A deterministic policy engine approves or blocks them.
- The LLM injection check only flags risk with reasons; code combines flags with policy to decide.
- Every number on screen comes from code. If any LLM-written sentence contains a digit, drop it.

## Layers
1. **Policy engine (deterministic):** per-agent daily budget, per-merchant limits, merchant allowlist, human-approval threshold, duplicate/replay window, velocity limits. A single shared `validatePayment()` that every path goes through.
2. **Injection check (LLM + heuristics):** reads the purchase context (merchant page text, tool output, agent's reasoning) for instructions that try to change the agent's goal or limits ("ignore your budget", "approved by admin"). Outputs flag + reason.
3. **Mock settlement ledger:** fake money only, clearly labelled.
4. **AML monitoring (reuse ComplianceGuard's rule engine where it fits):** structuring (splitting a purchase to stay under limits), velocity spikes, round-amount patterns, look-alike merchants (edit distance and homoglyphs), bursts of new merchants, dormant-then-active agents.
5. **AI investigator:** for each alert, drafts a short case note that cites only transaction IDs from the ledger. Code checks every cited ID exists and every number matches the ledger before showing the note.

## Stack ($0, same as Nakul's other projects)
- Static web frontend + Python serverless functions on Vercel (like SearchIQ). Move off Streamlit (it sleeps).
- LLM: gpt-oss-120b / gpt-oss-20b via Groq (free key) for the live site; OpenRouter (prepaid, pinned to Groq, no fallbacks) for evals. Keys only in env vars.
- Caps on the live site: per-visitor daily limit, site-wide daily limit, friendly limit message. The OpenRouter key's credit limit is the hard cap.

## Stage 1: Rebuild the core (no LLM yet)
- Port the AML rules from ComplianceGuard and the wallet/agent setup from AgentPay into one codebase.
- Build the policy engine, ledger and AML monitor with unit tests (every rule has a positive and negative test; `validatePayment()` is the only path to settlement).
- Remove Gemini; add an `LlmClient` with Groq/OpenRouter and a Mock implementation (tests use mocks).

## Stage 2: Red-team suite (publishable)
- Write a locked, versioned suite of 50 attack scenarios + 50 legitimate tasks. Suggested mix: 15 prompt injections (in merchant pages, tool outputs, invoices), 10 budget-splitting/structuring, 8 look-alike merchants, 7 bait-and-switch prices, 5 duplicate/replay, 5 approval bypass attempts. Each scenario: setup, the attack, expected outcome.
- Package it as a standalone JSON suite + small runner anyone can point at their own guardrails (MIT licence, clear README: "SafeSpend Red-Team Suite v1").
- Lock (commit) the suite before running anything against it.

## Stage 3: Evaluations
- **E1, red-team:** run the suite under four configs: no guardrails / policy only / policy + injection check / full (+ AML monitoring). Report attacks stopped, simulated money lost, false blocks on the 50 legitimate tasks, and how long AML took to flag what got through. Show results per attack category.
- **E2, public AML benchmark:** run the AML rules on a public labelled dataset. Prefer IBM's "Transactions for Anti Money Laundering" (synthetic, published for AML research; check licence and pick a manageable subset). Report precision and recall per pattern against the labels, next to a simple baseline (e.g. amount threshold only). Label it "synthetic public benchmark".
- **E3, investigator notes:** for 30 alerts, measure citation accuracy (every cited transaction exists and supports the claim; every number matches). LLM judge plus 10 notes for Nakul to hand-score.
- Write eval/README.md: method, results tables, charts, honest limitations (mock money, synthetic benchmark, small suite).

## Stage 4: Design approval, then ship
- Run the Design-first steps above and stop for approval before building UI.
- Landing: one sentence on what it does; a "Run the red-team" button that replays results live (from cache by default); a sandbox where visitors write their own injection attempt and see whether SafeSpend blocks it (counts against caps).
- Results page, a Track Record page like SearchIQ's, and a case study (problem, design, evals, failures found and fixed).
- Clear visual design: read the frontend-design guidance; buttons at least 44px, strong contrast, obvious primary actions, good phone layout. Show Nakul desktop and phone screenshots before deploying.
- Deploy on Vercel; run the checklist on the live URL.
- Update the old agentpay-ai and Complianceguard-ai READMEs to point to SafeSpend.


## Wall Street-grade requirements (these are what make it credible to bank, payments and fintech reviewers)
1. **Controls, not just checks.**
   - Maker-checker (four-eyes): payments above the approval threshold need a human approver who is not the requesting agent's owner; an agent can never approve its own payment (segregation of duties).
   - Every decision gets a reason code (e.g. BUDGET_EXCEEDED, LOOKALIKE_MERCHANT, INJECTION_SUSPECTED, SANCTIONS_HIT), like adverse-action codes.
   - Tamper-evident audit log: each decision record is hash-chained to the previous one; a "verify log" check proves nothing was edited. Exportable for auditors.
   - Circuit breaker: if spending velocity or alert volume spikes past a set level, all agent spending pauses until a human resumes it.
2. **A double-entry ledger.** Every payment is two balanced entries; property-based tests prove balances always reconcile and never go negative.
3. **Real sanctions screening.** Screen merchant and counterparty names against the public OFAC SDN list (download the official file; record its date). Use fuzzy matching and measure match precision and recall on a labelled test set of exact names, misspellings, transliterations and clean names.
4. **Metrics a risk team uses, not only precision and recall.**
   - Capacity-constrained detection: "if analysts can review K alerts a day, what share of bad activity is caught?" (precision and recall at a fixed alert budget, for several K).
   - Cost-based thresholds: choose the operating point by expected loss prevented vs. cost of false blocks and analyst time (state the cost assumptions, labelled ASSUMPTION). Show the curve.
   - False-positive rate and alert-to-case rate, the numbers AML teams are judged on.
5. **Adaptive-adversary stress tests.** Attackers who learn the limits: structuring just under thresholds, slow drip over many days, rotating look-alike merchants, injections reworded to evade the check. Plus a volume stress test (10× normal transactions). Report how detection degrades.
6. **Latency like a real authorization path.** Deterministic policy runs first (target p95 under 100 ms); the LLM injection check runs only when the context is risky or the payment is borderline. Measure and report p50/p95 latency and the share of payments that needed the LLM.
7. **Model risk documentation.** A short model validation report in the style of US bank model-risk guidance (SR 11-7): purpose and limits, conceptual soundness, data, outcomes analysis (the evals), sensitivity, ongoing monitoring plan, known weaknesses. Plus a control matrix: risk → control → test → evidence, mapping guardrails to the OWASP Top 10 for LLM Applications (e.g. prompt injection, excessive agency) and AML controls to FATF / FinCEN red-flag typologies.
8. **A risk-committee dashboard.** One screen a Head of Risk would read: losses prevented, residual risk, alert backlog, false-positive rate, top typologies, circuit-breaker status.

## Design-first (lesson from Rush Hour Lab): no UI code before Nakul approves the design
Before any frontend code, produce for approval:
- Three personas and their one main job: Head of Risk (is it safe? dashboard), Compliance analyst (work the alert queue), Developer (run the red-team against my agent).
- One user journey per persona, as numbered steps.
- Low-fidelity wireframes (desktop and phone) for: landing, risk dashboard, alert queue + case note, red-team runner, injection sandbox.
- A design token sheet (colors, type, spacing) following the frontend-design guidance: finance-grade density, clear tables, strong contrast, buttons at least 44px, no default-looking components.
After the UI is built: a 3-task usability check (each persona's main job) with screenshots on desktop and phone, and a list of what was confusing and fixed. Only then deploy.

## Honesty rules
- Mock money only; say so on every screen with money.
- Label every number's source: SIMULATED, BENCHMARK (named dataset), or MEASURED (eval).
- The ComplianceGuard results (49,937 transactions, $14.98M flagged, 6,948 → 26) came from its own generated data; never present them as real bank data.
- No real personal data anywhere.

## Copy rules
Plain, specific, active voice. No hype words (revolutionary, seamless, cutting-edge, leverage, robust). Sentence case.
