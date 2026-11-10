# Notes for later stages (from Nakul, 2026-11-10)

- **Stage 3, look-alike false positives:** measure the look-alike check's false-positive rate on a list of real, legitimate merchant names (not just the fictional demo set).
- **Stage 4, persistence:** use Turso (as in SearchIQ) for the ledger, audit log, idempotency store and approvals. Stage 1 keeps everything in memory.
- **Before the 10x stress test:** add running totals (per agent / owner / merchant per day and per window) so checks stop rescanning the whole ledger on every payment.
- **Stage 1 choices, approved:** `validate_payment()` naming; a blocked result is final per idempotency key; an expired approval returns to pending, an altered or reused one blocks; daily budgets reset at 00:00 UTC, velocity uses rolling windows; ComplianceGuard's geography/CTR/layering/round-trip rules not ported.
