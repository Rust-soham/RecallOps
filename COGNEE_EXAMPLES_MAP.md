# Cognee examples map for the hackathon build

This is the actual build reference. The Coral winner repos are only a quality/presentation bar; the project implementation should lean on Cognee’s own examples, integrations, and hackathon templates.

Initial examples sweep: 2026-06-29. Cognee integrations and Hermes Agent were
refreshed on 2026-06-30 after the kickoff.

## Short conclusion

The RecallOps cross-agent memory idea maps directly onto first-party Cognee
patterns:

```text
agent trace / conversation
  -> Cognee session memory
  -> extracted agent guidance / coding rules
  -> improve or distill into graph
  -> recall from a fresh agent session
  -> feedback / lint / supersede / forget
```

The project should not be built as generic “agent memory dashboard.” It should be a Cognee-native memory lifecycle cockpit for coding agents.

## Highest-value examples to copy first

| Need in our project | Cognee reference | What to steal |
| --- | --- | --- |
| Minimal memory lifecycle | `cognee/examples/demos/remember_recall_improve_example.py` | Clean `remember` permanent memory, `remember(..., session_id=...)` session memory, `recall`, `improve`, `forget` flow. |
| Explain session-to-graph promotion | `cognee/examples/demos/session_flow_stepwise_demo.py` | Narrated trace: seed permanent memory, absorb session guidance, call `improve(session_ids=[...])`, verify in fresh session. |
| Prove distillation | `cognee/examples/demos/session_distillation_demo.py` | Print distilled lesson documents, then query with a fresh verification session. |
| Learn from tool traces | `cognee/examples/demos/agentic_session_context_demo.py` | Use `TraceEntry`, store traces in session memory, extract agent-profile guidance, recall it with `scope=["session_context"]`, then distill. |
| Two-agent story | `cognee/examples/guides/agent_memory_quickstart.py` | One agent has session memory; another graph-only agent fails first, then succeeds after session traces persist into graph. This is the cleanest judge mental model. |
| Coding-agent-specific rules | `cognee/examples/custom_pipelines/memify_coding_agent_rule_extraction_example.py` | Extract coding rules from conversations into a `coding_agent_rules` node set; query with `SearchType.CODING_RULES`. |
| Feedback UI skeleton | `cognee/examples/demos/session_feedback_lifecycle_demo/` | FastAPI backend + frontend with graph snapshot, session Q&A, feedback, memify pipeline, before/after deltas. |
| Feedback affects retrieval | `cognee/examples/demos/feedback_score_shifting_example.py` | Positive/negative feedback changes graph weights and retrieval order. Strong before/after evidence. |
| Skill self-improvement | `cognee/examples/demos/skill_feedback_loop/skill_feedback_loop_demo.py` | Ingest skills, run weak task, record `SkillRunEntry`, generate proposal, apply improved skill. Useful if we want to show “agent got better at handoffs.” |
| Provenance graph | `cognee/examples/python/memory_provenance_demo.py` | Tenant/user/agent/session/dataset/data/memory-node projection; best reference for our “why does it believe this?” dashboard. |
| Multi-scope memory | `cognee-integrations/integrations/openclaw/README.md` and `src/plugin.ts` | Company/user/agent dataset scopes, scope-aware recall, file sync, `improve` on session end. Useful architecture even if we do not use OpenClaw. |
| Codex adapter | `cognee-integrations/integrations/codex/README.md` and plugin files | Existing Codex hooks for prompt/tool/answer capture, context injection, idle/session-end sync, logs/statusline. Use this rather than writing Codex capture from scratch. |
| OpenCode adapter | `cognee-integrations/integrations/opencode/README.md` and `src/plugin.ts` | Existing OpenCode auto-capture, auto-recall, idle improve, `cognee_remember`, `cognee_search`. Use same project dataset as Codex. |
| Optional Hermes client | `cognee-integrations/integrations/hermes-agent/README.md` and `provider.py` | Existing Hermes session capture, recall, remember, forget, and session-end improve. Reuse after the two-agent MVP; do not build an adapter. |
| Hackathon submission grammar | `cognee-hackathons/cognee-cloud-hackathon-2026-06-19/templates/SUBMISSION.md` | Ingest / Query + Self-improve / Lint, baseline vs improved run, what changed in the brain. |

## What this means for our product

### The demo should be Cognee lifecycle-first

The visual output should make these state transitions obvious:

```text
Captured trace
  -> session memory
  -> agent guidance / coding rule
  -> promoted graph memory
  -> recalled by a different agent
  -> refined by feedback
  -> stale memory superseded or forgotten
```

The dashboard is proof, not the whole product.

Judges should understand in 10 seconds:

> Codex learned a project rule. OpenCode used it in a fresh session. Cognee preserved and improved the memory.

### We should reuse official integrations

The fastest credible build path:

1. Use the Codex Cognee plugin/hook pattern to capture:
   - user prompts
   - tool traces
   - assistant responses
   - recall counts/audit logs
2. Use the OpenCode Cognee plugin pattern for:
   - `tool.execute.after` capture
   - `cognee_remember`
   - `cognee_search`
   - idle `improve`
3. Force both to use one project dataset:
   - e.g. `COGNEE_PLUGIN_DATASET=recallops-demo-auth`
4. Build our dashboard/service around:
   - Cognee session entries
   - agent traces
   - graph snapshots / recalled memory
   - manual promotion/supersede/forget actions

This lets us spend hackathon time on the product layer rather than basic agent plumbing.

Both agents must talk to one Cognee HTTP service. The kickoff warned that
multiple agent threads can lock Cognee's default local file databases. Use a
single local server during development and Cognee Cloud/Postgres for the
submitted multi-agent deployment.

## Exact implementation patterns to borrow

### 1. Trace capture from `agentic_session_context_demo.py`

The demo uses:

```python
from cognee.memory import TraceEntry

await cognee.remember(
    TraceEntry(
        origin_function="run_tests",
        status="error",
        method_params={"command": "pytest -q"},
        error_message="ModuleNotFoundError: No module named 'dotenv'",
    ),
    dataset_name=DATASET_NAME,
    session_id=SESSION_ID,
    self_improvement=False,
    user=user,
)
```

For RecallOps, each agent tool call can become a `TraceEntry`:

- `origin_function`: tool name, e.g. `exec_command`, `apply_patch`, `read_file`
- `status`: success/error
- `method_params`: command/path/args
- `method_return_value`: clipped output or summary
- `error_message`: failure text

Dashboard copy:

> Raw agent traces become session memory. Cognee extracts reusable guidance from them.

### 2. Agent guidance recall from `agentic_session_context_demo.py`

The demo recalls agent-profile guidance using:

```python
await cognee.recall(
    "what should I know before running tests in this repo?",
    scope=["session_context"],
    context_profile="agent",
    session_id=SESSION_ID,
    only_context=True,
    user=user,
)
```

For us:

- before a new agent starts, ask for “what should this coding agent know before editing auth/logout?”
- inject the returned guidance into Codex/OpenCode and optional Hermes.

Dashboard copy:

> This is not chat history. It is extracted operational guidance for future agents.

### 3. Session-to-graph proof from `session_distillation_demo.py`

The key visible proof:

1. run a session
2. print/show session guidance
3. distill into graph
4. query from a fresh session

For our canonical demo:

```text
Session A learned:
  "Auth uses HTTP-only cookie sessions; do not reintroduce JWT localStorage."

Fresh Session B asks:
  "How should logout work?"

Fresh Session B recalls:
  "Use cookie session clearing + server-side refresh revocation."
```

### 4. Coding rules from `memify_coding_agent_rule_extraction_example.py`

The example takes coding conversations and creates specific rule nodes:

- principal engineer / manager say rules
- `memify(...)` extracts rules
- rules are stored in `coding_agent_rules`
- `recall(..., query_type=SearchType.CODING_RULES, node_name=["coding_agent_rules"])`

For RecallOps:

- conversations/tool traces mention repo-specific rules
- extract durable `CodingRule` memories
- show rules as a separate dashboard lane:
  - “Auth: HTTP-only cookie sessions”
  - “Tests: use `uv run pytest`, not plain pytest”
  - “Do not store tokens in localStorage”

This is more Cognee-specific than a generic notes list.

### 5. Feedback and graph deltas from `session_feedback_lifecycle_demo`

This demo already has:

- `/demo/session`
- `/demo/graph`
- `/demo/feedback`
- `/demo/run_memify_pipeline`
- before/after graph snapshots
- changed node/edge deltas

For us:

- “approve memory” = positive feedback / promotion
- “reject stale memory” = negative feedback or supersede marker
- `run_memify_pipeline`/`improve` = visible improvement step
- dashboard shows “3 nodes changed, 2 edges changed”

Judge-facing line:

> Feedback is not cosmetic; it changes what Cognee retrieves next.

### 6. Skill self-improvement from `skill_feedback_loop_demo.py`

This is optional but high-ceiling.

It demonstrates:

- ingesting skills from a folder
- running an agentic task against those skills
- recording `SkillRunEntry`
- generating an improvement proposal
- applying it with `improve_skill(...)`

For our project, the analogous skill could be:

```text
handoff-writer/SKILL.md
```

Weak v1 skill:

> Summarize what happened.

Improved skill:

> Include active decisions, superseded facts, unresolved questions, files touched, and verification state.

This would let us show the “handoff agent” itself improving.

De-scope unless core cross-agent memory works first.

## Dashboard shape from Cognee references

Borrow from `session_feedback_lifecycle_demo`, but reshape it for agent memory:

### Left: Agent timeline

```text
Codex session
  trace: read stale docs
  trace: patched logout
  learned: auth uses cookie sessions
  promoted: yes

OpenCode session
  recalled: auth uses cookie sessions
  trace: implemented logout

RecallOps review
  referenced: source security decision
  superseded: stale JWT/localStorage claim
  improved: active cookie-session rule
```

### Middle: Memory cards

Each card:

- statement
- kind: decision / coding rule / failure / fix / assumption
- status: session-only / proposed / promoted / superseded / rejected / forgotten
- learned by: agent + session
- evidence: trace IDs, files, commands, answer snippets
- used by: later agents / recalls

### Right: Cognee inspector

Show the sponsor-tech proof:

- dataset
- session ID
- source: session / trace / graph / session_context
- `remember` call count
- `recall` hit count
- `improve`/distillation status
- graph deltas after feedback

## Canonical demo script using Cognee examples

### Act 1 — Codex learns a repo rule

Reference:

- `integrations/codex`
- `agentic_session_context_demo.py`
- `memify_coding_agent_rule_extraction_example.py`

Action:

- Codex reads a stale note saying auth uses JWT/localStorage.
- Current code/tests show the app uses HTTP-only cookie sessions.
- Codex records a trace and explicit memory:
  - “Auth uses HTTP-only cookie sessions; do not reintroduce JWTs in localStorage.”

Cognee proof:

- show `TraceEntry`
- show session memory / agent guidance
- show the proposed coding rule

### Act 2 — Promote into graph

Reference:

- `remember_recall_improve_example.py`
- `session_distillation_demo.py`
- `session_flow_stepwise_demo.py`

Action:

- click “Promote / improve”
- call `improve(dataset=..., session_ids=[...])` or distillation path
- memory becomes durable graph knowledge

Cognee proof:

- card moves from `session-only` to `promoted`
- graph snapshot / recall result shows durable memory

### Act 3 — OpenCode uses it fresh

Reference:

- `integrations/opencode/src/plugin.ts`
- `agent_memory_quickstart.py`

Action:

- OpenCode starts with no chat history.
- User asks it to implement logout.
- OpenCode recalls the auth rule from shared Cognee dataset.
- It avoids JWT/localStorage and implements cookie/session revocation path.

Cognee proof:

- dashboard shows a recall event from OpenCode using a memory learned by Codex.

### Act 4 — Audit/refine

Reference:

- `session_feedback_lifecycle_demo`
- `feedback_score_shifting_example.py`

Action:

- RecallOps displays the conflicting claims and Cognee source references.
- A human approves the active rule and records the refinement:
  - “Logout must clear cookie and revoke server-side refresh session.”
- dashboard marks older memory as superseded and promotes the refined memory.

Cognee proof:

- before/after: old memory lower priority/superseded, corrected memory active
- optional graph deltas / feedback weights changed

### Act 5 — Fresh session recall

Reference:

- `session_distillation_demo.py`
- `agent_memory_quickstart.py`

Action:

- start a brand-new Codex/OpenCode session
- ask: “What should I know before editing auth/logout?”
- it recalls the corrected memory.

Close line:

> Codex learned it. RecallOps verified it. OpenCode used it. Cognee made the
> truth durable.

## What to de-scope

Do not spend early time on:

- big graph visualization as the hero
- full automatic conflict resolution
- Hermes integration before Codex → OpenCode works
- large codebase ingestion
- generic MCP server for all agents
- Obsidian plugin

The Cognee examples say the winning demo is about the memory lifecycle, not breadth.

## Useful commands / files during implementation

### Codex plugin reference

```text
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/codex/README.md
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/codex/plugins/cognee/hooks.json
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/codex/plugins/cognee/scripts/session-context-lookup.py
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/codex/plugins/cognee/scripts/store-to-session.py
```

### OpenCode plugin reference

```text
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/opencode/src/plugin.ts
/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/opencode/src/client.ts
```

### Demo UI/backend reference

```text
/tmp/cognee-reference-2026-06-29/cognee/examples/demos/session_feedback_lifecycle_demo/backend/app.py
/tmp/cognee-reference-2026-06-29/cognee/examples/demos/session_feedback_lifecycle_demo/frontend/
```

### Agent trace / session context reference

```text
/tmp/cognee-reference-2026-06-29/cognee/examples/demos/agentic_session_context_demo.py
/tmp/cognee-reference-2026-06-29/cognee/examples/guides/agent_memory_quickstart.py
```

### Coding rules / memify reference

```text
/tmp/cognee-reference-2026-06-29/cognee/examples/custom_pipelines/memify_coding_agent_rule_extraction_example.py
```

### Submission reference

```text
/tmp/cognee-reference-2026-06-29/cognee-hackathons/cognee-cloud-hackathon-2026-06-19/templates/SUBMISSION.md
```
