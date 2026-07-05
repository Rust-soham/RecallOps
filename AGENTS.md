# RecallOps agent guidance

RecallOps is the reviewed memory layer for this project.

- At the start of a task, use `recallops_recall` or `recallops_handoff` for
  relevant current project decisions.
- Use `recallops_record` only for durable decisions, constraints, failures,
  fixes, assumptions, or open questions that would help a future agent.
- Every recorded memory needs a concrete evidence file or URI.
- Never record secrets, credentials, raw command output, or transient chatter.
- A recorded memory is only a candidate until a human approves it in the
  RecallOps dashboard.

For the canonical demo, use project ID `auth-migration`.

