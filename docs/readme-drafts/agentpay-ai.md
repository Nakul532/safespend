> **This project now lives on in [SafeSpend](SAFESPEND_URL).**
> AgentPay showed AI agents paying for APIs. SafeSpend is the next step: the controls layer that decides whether an agent may pay at all.
> - Every payment goes through one deterministic policy engine (budgets, allowlists, four-eyes approval, duplicates, velocity); the LLM can only flag risk, and code decides.
> - Gemini is replaced by gpt-oss on Groq; the mock USDC ledger became a double-entry ledger with a hash-chained audit log.
> - It is tested against a locked red-team suite and held-out attack sets, with results published (simulated money only).
> - Try to trick its purchasing agent yourself in **Break the bank**.
>
> This repository is kept as the original prototype and is no longer maintained.

---
