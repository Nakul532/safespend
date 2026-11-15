# Control matrix

Risk → control → test → evidence. Guardrails map to the OWASP Top 10 for LLM Applications (2025); AML controls map to FATF and FinCEN red-flag typologies. All money is simulated.

| Risk | Framework | Control | Test | Evidence |
|---|---|---|---|---|
| Prompt injection in a page, invoice or tool output changes the agent's goal | OWASP LLM01 Prompt injection | Injection check: hidden text blocks; heuristic or model flags hold for a human | Red-team injection category, held-out sets | E1 results by category; tests/test_after_lock.py |
| Agent spends beyond what it should | OWASP LLM06 Excessive agency | Per-payment limit, daily budget, team budget, merchant allowlist, velocity limit | Suite v1 budget and approval categories | E1; tests/test_policy.py |
| Approval claimed in text ("approved by the CFO") | OWASP LLM06; segregation of duties | Four-eyes approval: signed, bound to the payment hash, expiring, never from the owner | Approval-bypass category; game Level 1 | tests/test_idempotency_and_approvals.py; Level 1 |
| Model output trusted as a decision | OWASP LLM05 Improper output handling | The LLM only flags; code decides; fail closed; no model-written numbers shown | Mocked failure tests | tests/test_after_lock.py, tests/test_intent.py |
| Purchase differs from what the person asked | OWASP LLM06; LLM09 Misinformation | Intent check (fields + model flag) | Locked intent set (26) | eval/results/intent_locked.json |
| Bait-and-switch price | OWASP LLM06 | Charged amount must not exceed the quote | Price category | E1 |
| Free trial converts / auto top-up / saved card | OWASP LLM06 | Recurring-commitment and stored-credential holds | Owner incidents; tests | tests/test_commitments.py; C5 results |
| Duplicate or replayed payment | Payments control | Idempotency keys required; duplicate heuristic | Duplicate/replay category | E1; tests/test_idempotency_and_approvals.py |
| Look-alike merchant | FATF/FinCEN: fraud-linked payees | Look-alike detection (edit distance, homoglyphs) | Look-alike category; SEC false-positive test | eval/results/lookalike_fp.json |
| Sanctioned counterparty | OFAC screening | Fuzzy sanctions screening with transliteration | Sanctions category; dev set | E1; eval/dev/sanctions_dev.json |
| Structuring to stay under thresholds | FinCEN structuring red flag (31 USC 5324) | Pre-payment split check; AML structuring and team-structuring rules; AML→hold | Structuring category; IBM benchmark | E1 round 2; E2 |
| Rapid draining / velocity | FATF rapid movement of funds | Velocity limits; rapid-fire and velocity-spike rules; circuit breaker | IBM retune; game Level 2 | eval/results/e2_rapidfire.json |
| Funnel / mule accounts | FATF funnel-account typology | Fan-in rule | IBM recall by pattern | E2 |
| Dormant account suddenly active | FinCEN red flag | Dormant-then-active rule | Synthetic data, tests | tests/test_aml.py |
| Cash-out via gift cards, crypto, transfers | FinCEN advisories on gift-card fraud | High-risk category rule; intent field check on cash equivalents | Synthetic data; intent set | tests; intent results |
| Tampered records | Audit and record-keeping | Hash-chained audit log with verification and export | Tamper tests | tests/test_ledger_audit_breaker.py |
| Unexplained alert decisions | Model risk (SR 11-7) | Reason codes on every decision; code-computed evidence pack; investigator notes checked against it (citations, no model numbers, claim checks) | E3 v4 (31 alerts) and earlier versions | eval/results/e3_v4.json, e3_v3.json |
| Unbounded LLM cost on the public site | OWASP LLM10 Unbounded consumption | Per-visitor, per-IP and site-wide daily caps | Cap tests | web/store.py |
| Personal data in visitor submissions | Privacy | Opt-in only, text-only, scrubbed, human review, deletion by ID | Scrub tests | web/store.py; /privacy |
