# Notes for later stages (from Nakul, 2026-11-10)

- **Stage 3, look-alike false positives:** measure the look-alike check's false-positive rate on a list of real, legitimate merchant names (not just the fictional demo set).
- **Stage 4, persistence:** use Turso (as in SearchIQ) for the ledger, audit log, idempotency store and approvals. Stage 1 keeps everything in memory.
- **Before the 10x stress test:** add running totals (per agent / owner / merchant per day and per window) so checks stop rescanning the whole ledger on every payment.
- **Stage 1 choices, approved:** `validate_payment()` naming; a blocked result is final per idempotency key; an expired approval returns to pending, an altered or reused one blocks; daily budgets reset at 00:00 UTC, velocity uses rolling windows; ComplianceGuard's geography/CTR/layering/round-trip rules not ported.

## Deploy-time order (from Nakul, 2026-11-14)
1. Run a secrets scan across the **full git history**: API keys, `.env`, the SEC contact (`SEC_USER_AGENT`), raw IBM/SEC data, raw held-out `*-raw.txt` files. Show Nakul the result.
2. Nakul makes the repo public.
3. Then fill `SAFESPEND_URL` and the repo link in the approved README notices (`docs/readme-drafts/`) and push them to agentpay-ai and Complianceguard-ai. Not before.

## Naming (2026-11-15)
- The project is SafeSpend ("Spending controls for AI agents"); GitHub repo Nakul532/safespend. It was called AgentGuard until 2026-11-15; commit history, the frozen evaluation tags and the locked v1 suite files keep the old name.
- Vercel project name: `safespend`.

## Deployed (2026-11-16)
- Production: https://safespend-nakul.vercel.app (Vercel project `safespend`, deploys on push to main). `/api/health` reports database and key status without values.
- README notices with the live URL and repo link pushed to agentpay-ai and Complianceguard-ai.
