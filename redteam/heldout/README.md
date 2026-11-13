# Held-out attack sets

Rules:
- **Never used while developing a guardrail.** Don't read these files when building or tuning AgentGuard. Run them only to produce reported results.
- **Each set is locked in its own commit** with its own lock file of SHA-256 hashes. A set is never edited after locking; fixes go in a new version.
- **Reported as its own column,** next to the main suite.

| File | Source | Attacks | Lock |
|---|---|---|---|
| `heldout-model-v1.json` | A separate model session (Claude Sonnet). It got only the world and the format, with no access to the suite or AgentGuard code, and made one file write. | 18 | `LOCK.json` |
| `heldout-owner-v1.json` | "owner-sourced incidents, drafted with Claude (same model family as the builder; not human-written, not independent)" | 5 | `LOCK-owner.json` |
| `heldout-external-v1.json` | As given in the file's `label` field (copied verbatim from the source) | 6 | `LOCK-external.json` |

## How the owner and external sets were made
- **Conversion:** the project owner supplied raw text files (`*-raw.txt`, git-ignored). A fresh agent converted each one to the format in `../SCHEMA.md`. Each agent could read only its own raw file, `SCHEMA.md` and `world-v1.json`, and write only its output file. The tool logs confirm this.
- **Unread by the builder:** the AgentGuard developer (Claude) never read the raw files or the converted scenarios. It checked them by script, for counts, validation errors and the masked shape of invalid values only.
- **Missing capabilities:** every scenario in both sets has a `missing_capabilities` list and `unmodelled_details`. These describe what the world can't model yet, kept at full strength rather than simplified. There are 16 capability tags in the owner set and 21 in the external set.
- **Gaps filled during conversion, as reported by the converters:**
  - Owner set: the raw text didn't name merchants or say whether they were allowlisted. Each scenario got a generic new merchant added to procurement-agent's allowlist, and one invoice reference is a placeholder.
  - External set: several scenarios had no amounts or vendor names, so placeholder amounts and new merchants were used. Some vendors were allowlisted where the test needed an otherwise acceptable vendor. One step's task was missing and is "Not stated in source."
  - Each placeholder is noted in its scenario's `description` or `unmodelled_details`. These choices can change difficulty, and only the owner has checked them against the incidents.
- **Format changes:**
  - Validation first found $0 amounts in two owner-set steps, so the format now allows $0 (for example, a free sign-up or card check that sets up later charges).
  - It also found an approval from a person outside the world in the external set, so the format now accepts any approver name.
  - The files themselves were not edited for these.

`world-v1.json` here is a byte-identical copy of `../suite/world-v1.json`.
