# Held-out attack sets

Rules:
- **Never used while developing a guardrail.** Don't read these files when building or tuning AgentGuard. Run them only to produce reported results.
- **Each set is locked in its own commit,** and `LOCK.json` holds its hashes. A set is never edited after locking; fixes go in a new version.
- **Reported as its own column,** next to the main suite.

| File | Written by | Scenarios | Status |
|---|---|---|---|
| `heldout-model-v1.json` | A separate model session (Claude Sonnet). It got only the world and the format, with no access to the suite or AgentGuard code, and made one file write. | 18 attacks | Locked |
| `heldout-owner-v1.json` | The project owner | 5 attacks (to write) | Template, not locked yet |

The AgentGuard developer (Claude) checked the model-written set only by script: counts and validation errors, never scenario content. Its 4 initial validation errors all came from attaching an approval to the current step. The format was widened to allow that ("approval claimed without a prior hold"); the file itself was not edited.

`world-v1.json` here is a byte-identical copy of `../suite/world-v1.json`.
