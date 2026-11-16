# SafeSpend

**Spending controls for AI agents.** Live: https://safespend-nakul.vercel.app · A payment firewall and anti-money-laundering monitor for AI agents. All money is simulated (mock only).

Status: **Stage 1, the core engine.** There is no UI and no live LLM calls yet.

## How a payment flows

1. An agent sends a `PaymentRequest` with an idempotency key.
2. `PolicyEngine.validate_payment()` runs every check in a fixed order (`policy.CHECK_ORDER`). The first failing check decides the outcome, and the audit record lists every check that failed.
3. Only an `APPROVED` decision carries a signed `SettlementPermit`. The double-entry `Ledger` settles nothing without one, and each permit works once.
4. Payments at or above an agent's approval threshold wait for a human. The approver can't be the agent's owner. Each approval is signed and bound to the exact payment, and it expires after a set time.
5. `AmlMonitor` scans settled payments for 10 patterns, including team-level structuring across agents with the same owner.
6. A circuit breaker pauses all spending when spend or alert volume spikes. Resuming needs an approver who doesn't own any agent involved.
7. Every decision, approval, settlement, alert and breaker event is written to a hash-chained audit log, along with the policy version and policy hash.

## Layout

| Path | What it is |
|---|---|
| `safespend/policy.py` | Policy engine and `validate_payment()` |
| `safespend/ledger.py` | Double-entry mock ledger |
| `safespend/approvals.py` | Maker-checker approvals |
| `safespend/idempotency.py` | Idempotency-key store |
| `safespend/circuit_breaker.py` | Spend and alert circuit breaker |
| `safespend/audit.py` | Hash-chained audit log, with verify and export |
| `safespend/aml/` | AML rules and monitor |
| `safespend/lookalike.py` | Homoglyph and edit-distance merchant matching |
| `safespend/sanctions.py` | Sanctions-screening interface (real OFAC list comes later) |
| `safespend/llm/` | `LlmClient`: Groq, OpenRouter (pinned to Groq, no fallbacks), Mock |
| `safespend/clock.py` | Injectable UTC clock |
| `safespend/fixtures.py` | Demo agents and merchants from AgentPay |
| `refs/` | Read-only clones of ComplianceGuard and AgentPay (git-ignored) |

## Run the tests

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

Keys (`GROQ_API_KEY`, `OPENROUTER_API_KEY`) are read only from environment variables. The tests never call a real LLM.

## Red-team suite

`redteam/` holds the SafeSpend Red-Team Suite v1: 55 attacks and 55 legitimate tasks, a runner, and held-out sets. It is MIT-licensed and self-contained. See `redteam/README.md`.

### Held-out sets are now public

The v1 held-out sets (model-written, external-model and owner-sourced incidents) and the intent-mismatch set are published here together with their results. Once public they can no longer serve as held-out tests: anyone, including future builders, can read and tune against them. **Any future version of SafeSpend needs new held-out attacks**, written independently, locked before evaluation and run once, to make a fresh claim. Results on the v1 sets after publication should be read as regression checks, not as held-out evidence.
