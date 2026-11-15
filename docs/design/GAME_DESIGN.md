# SafeSpend: game design v2 (replaces the dashboard-style design)

## Positioning
Stripe, Visa, Mastercard, Coinbase and Google are building the rails that let AI agents pay (Stripe/Tempo Machine Payments Protocol, Visa Intelligent Commerce and Trusted Agent Protocol, Mastercard Agent Pay, Coinbase x402, Google AP2). Every company using those rails still needs the controls: what an agent is allowed to pay for, and how abuse gets caught. SafeSpend is that controls layer. The game makes it tangible.

## Mode 1: "Break the bank" (you play the attacker)
The visitor tries to trick a company's AI agent into wasting money. Each level is a real 2026 scenario and adds one defence. Every outcome comes from the real SafeSpend engine (no scripted results). Simulated money only, labelled everywhere.

| Level | Scenario (modelled on) | What the visitor tries | Defence introduced | Lesson revealed |
|---|---|---|---|---|
| 1. The accounts-payable agent | An AI paying a company's vendor invoices (Ramp-style AP automation) | A fake "urgent, approved by the CFO" invoice | Four-eyes approval: approval must come from the system, never from text | Approvals can't be claimed in an email |
| 2. The pay-per-call drain | An agent paying per API call (Stripe MPP / Coinbase x402-style micropayments) | Thousands of tiny charges that add up | Velocity limits + cumulative per-merchant checks (structuring at machine speed) | Small payments can hide big theft |
| 3. The travel agent | An agent booking a ride or hotel (like Mastercard Agent Pay's first live taxi booking) | A look-alike merchant ("Uber Premium Rides Ltd", homoglyphs) | Look-alike detection + trusted merchant registry | Names that look right can route money elsewhere |
| 4. The free-trial trap | An agent signing up for developer tools | A $0 trial that silently converts to a paid plan, a pre-ticked auto top-up | Recurring-commitment and stored-credential holds | $0 today can mean unlimited later |
| 5. The intent mismatch | An agent buying for a person (the problem Mastercard's Verifiable Intent targets) | Get the agent to buy something the person never asked for, via an injected product page | Injection check + intent check against the original request | The agent must do what the human meant |
| Boss level | Everything on, adaptive | Any combination | Full SafeSpend | See the audit trail of every decision |

Per level:
- A short brief (one card): who the agent works for, its budget, its job.
- An attack composer: pick a template or write your own (invoice text, product page, merchant name, amount, number of payments). Templates make it playable in 10 seconds; free text makes it real.
- Press "Send to agent". The agent's proposed payment appears, then SafeSpend's decision lands as a rubber stamp: APPROVED, HELD or BLOCKED, with the reason code and the audit-log line sliding in.
- A running "money protected" vault total and a "money lost" total.
- Winning a level (an attack gets through) reveals which defence in a later level would have stopped it.
- Consent checkbox: "Let SafeSpend learn from my attack" stores the attack text (no personal data, moderated, capped) for a future visitor-submitted held-out set.

## Mode 2: "Analyst shift" (you play the defender)
You're an AML analyst with a 3-minute shift and room to review 15 alerts out of a stream of 60 (built from the real rules on synthetic data, including IBM-style patterns). Pick what to open; each opened alert shows the evidence and the AI investigator's case note with every cited transaction linked. Score: laundering caught, false alarms, money recovered. The end screen compares your picks with SafeSpend's ranked queue, teaching the real lesson from the IBM benchmark: with a limited review budget, ranking matters more than catching everything.

## Mode 3: "For professionals"
Results (red-team by set and config, held-out first), the IBM benchmark at alert budgets, latency, look-alike false positives, the model validation report and the control matrix. Calm, dense, printable.

## Visual design system (replace the current colours entirely)
Concept: a bank's back office, made playful. A warm ledger-paper base, ink-dark text, and rubber-stamp verdicts. Not dark-hacker, not neon.

Light theme (default):
- Background "ledger paper": #F4F1EA; surface cards: #FFFFFF with a 1px hairline #E3DED3
- Text "ink": #151A22; secondary text: #5B6270
- Interactive accent "bank indigo": #3D4FC9 (buttons, links, focus rings); hover #2F3FAE
- Verdicts (always paired with an icon and a word, never colour alone):
  - APPROVED "ledger green": #0E7C5A
  - HELD "amber stamp": #B7791F
  - BLOCKED "brick red": #B33A2E
- Money figures: ink, tabular numbers

Dark theme (for the analyst shift and if the visitor prefers dark):
- Background "vault night": #12161F; surfaces #1B2130; hairline #2A3243
- Text #ECEEF2; secondary #A4ACBA
- Accent #8B98F5; APPROVED #3FBF8F; HELD #E0A84A; BLOCKED #E06A5C

Contrast: every text/background pair meets WCAG AA (4.5:1 body, 3:1 large text); check and report the ratios.

Type:
- Headings and UI: IBM Plex Sans (600 for headings, 400/500 for body)
- Money, codes, audit-log lines: IBM Plex Mono with tabular figures
- Stamps: IBM Plex Sans Condensed, 700, uppercase, slight rotation (-4°), double border
- Sizes: 16px body, 14px secondary, headings 32/24/20, line-height 1.5 for body

Motion: stamp drops with a short bounce (150-250ms); audit lines slide in; vault counter ticks up. All motion off under prefers-reduced-motion.

Layout: one main action per screen; level cards on a horizontal "progress ledger" across the top; phone-first; buttons at least 48px tall; nothing scrolls sideways.

## Credibility rules
Real engine behind every outcome; simulated money labelled on every screen with money; no personal data; visitor attacks only with consent; held-out results shown before v1 results; known gaps (recurring charges, stored credentials, future liabilities) stated plainly where Level 4 touches them.
