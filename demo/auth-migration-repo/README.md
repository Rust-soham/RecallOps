# RecallOps auth migration fixture

This intentionally starts in a failing state. The stale implementation follows
`docs/legacy-auth.md`; the approved decision is in `docs/security-review.md`.

The canonical demo asks Codex to discover and record the approved rule, then
asks a fresh OpenCode session to implement `buildLogoutAction` using the
RecallOps handoff.

