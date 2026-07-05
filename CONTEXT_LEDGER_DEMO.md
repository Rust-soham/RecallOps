# RecallOps: Viable Cross-Agent Demo

Status: accepted implementation specification after kickoff transcript review

## One-sentence pitch

> The flight recorder and control plane for shared AI-agent memory: Codex
> learns it, RecallOps verifies it, OpenCode uses it, and Cognee makes it
> durable.

External product name: **RecallOps**. “Context Ledger” remains the internal
concept name only. Do not call any feature “Hermes”: Cognee has a real Hermes
Agent integration, and the name would create avoidable confusion.

## What the product is

RecallOps has three surfaces:

1. **Shared memory service** — Cognee stores session memory and the permanent
   project knowledge graph.
2. **Agent adapters** — Codex and OpenCode automatically capture useful
   session events and recall relevant project memory. Real Hermes Agent is an
   optional third client after v1 is stable.
3. **Human dashboard** — shows what crossed between agents, where each memory
   came from, what conflicts, and what became durable.

The memory service and adapters are the functional product. The dashboard is
the judge-readable proof and the human control surface.

RecallOps does not host or proxy the models. Codex and OpenCode keep using the
user's existing ChatGPT-subscription authentication. Hermes Agent can also use
its `openai-codex` OAuth provider if the stretch integration is enabled. The
agents call RecallOps/Cognee for memory, not model inference.

## The user problem

Developers switch between coding agents for different strengths, interfaces,
or rate limits. Each agent starts from the repository but not from the
reasoning that produced it:

- architectural decisions;
- failed approaches;
- environment quirks;
- user preferences;
- why an implementation looks unusual;
- unresolved blockers;
- lessons discovered in another agent's session.

Files preserve the result. They rarely preserve the useful working context.

## Architecture

```text
Codex RecallOps MCP ──────┐
                          ├──► RecallOps FastAPI ───► operational event log
OpenCode RecallOps MCP ───┘       │                       │
                                 │                       v
                                 │                 Web dashboard
                                 v
                        one Cognee HTTP service
                                 ▲
                                 │
        official Codex plugin ───┼── official OpenCode plugin
                                 │
                     official Hermes provider (stretch)
```

The operational store exists for low-latency UI state: connected agents,
events, pending approvals, and demo reset. Cognee remains the source of
long-term memory and retrieval.

All agents must connect to the same Cognee service endpoint. They must not open
the same local SQLite/Kuzu/LanceDB stores in separate processes. The kickoff
warned that concurrent agent threads can lock file-backed stores and
recommended FastAPI plus Postgres. Local development therefore uses one Cognee
server as the single owner; the submitted Cloud deployment uses Cognee Cloud
or a Postgres-backed service.

## Cognee memory model

One permanent dataset per project:

```text
project:<repository-identity>
```

One session id per agent run:

```text
codex:<host-session-id>
opencode:<session-id>
hermes:<session-id>
```

Core memory entities:

- `Project`
- `AgentRun`
- `Decision`
- `Constraint`
- `Assumption`
- `Failure`
- `Fix`
- `Artifact`
- `Evidence`
- `OpenQuestion`

Core relationships:

- `LEARNED_IN`
- `APPLIES_TO`
- `SUPPORTS`
- `CONTRADICTS`
- `SUPERSEDES`
- `CAUSED`
- `RESOLVED_BY`
- `TOUCHED`

Use Cognee session memory for raw and provisional experience. Promote reviewed
decisions, constraints, failures, and fixes into the permanent graph with
`improve(dataset=..., session_ids=[...])`.

## Agent tool contract

Keep the visible tool surface small.

### `recallops_recall`

```text
query
project
optional task
```

Returns a compact context pack:

- relevant current decisions;
- known constraints;
- prior failed approaches;
- unresolved questions;
- source agent/session;
- Cognee source references plus evidence path or commit;
- whether a memory is permanent or session-only.

### `recallops_record`

```text
kind: decision | constraint | failure | fix | assumption | question
statement
evidence
confidence
project
```

Writes a candidate memory into the current Cognee session. It does not silently
declare the candidate canonical.

### `recallops_handoff`

```text
project
goal
optional target_agent
```

Generates the smallest useful handoff for a new agent. This is a focused
retrieval operation, not a summary of the whole repository.

Human-only dashboard actions:

- Approve and promote
- Edit and promote
- Mark superseded
- Reject
- Forget session/data item

Agents may propose a conflict resolution but should not silently delete or
rewrite durable memory.

## Adapter plan

### Codex

Use the official Cognee Codex integration as the base rather than rebuilding
session plumbing.

Codex currently supports:

- local STDIO and streamable HTTP MCP servers;
- `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PreCompact`, and `Stop`
  hooks;
- adding recalled hook output as developer context;
- project-scoped plugin and MCP configuration.

The official Cognee Codex plugin already:

- captures prompts, tool traces, and assistant responses;
- injects context on prompt submit;
- syncs session memory into graph memory on exit/idle;
- uses the `agent_sessions` dataset by default.

RecallOps adds project and source-agent attribution plus the dashboard
event feed.

### OpenCode

Use the official `@cognee/cognee-opencode` plugin as the base.

It already:

- captures completed tool calls into Cognee;
- injects memory during compaction;
- exposes `cognee_remember` and `cognee_search`;
- supports local or remote Cognee.

OpenCode also supports local/remote MCP and plugin events for sessions,
messages, files, and tools. RecallOps adds consistent project/session
identity and dashboard events.

### Hermes Agent (stretch)

Use Cognee's official standalone Hermes memory provider:
`cognee-integration-hermes-agent`.

It already:

- stores each completed Hermes turn in Cognee session memory;
- uses session-first recall with graph fallback;
- exposes Cognee remember and forget tools;
- mirrors explicit Hermes memory writes;
- runs `improve()` when a Hermes session ends;
- supports local-server, remote/Cloud, and opt-in embedded modes.

Hermes supports an `openai-codex` provider through ChatGPT/Codex OAuth, so it
does not require the user to buy a separate model API subscription.

Do not fork Hermes, create a custom agent runtime, or build another adapter.
Point the official provider at the same project dataset and RecallOps/Cognee
service. Add Hermes only after Codex → OpenCode, provenance, improvement, and
the deterministic demo are reliable.

## Canonical demo story

Use a tiny prepared repository with a visible but understandable architectural
constraint.

Scenario:

- An older note says authentication uses JWTs in `localStorage`.
- The project has since moved to secure HTTP-only cookie sessions because of a
  security review.
- The implementation is partially migrated.

### Act 1 — Codex learns

In Codex:

```text
Finish the login migration and verify the tests.
```

Codex discovers the cookie-session decision, fixes one focused issue, and
records:

```text
decision:
Authentication uses HTTP-only cookie sessions. Do not reintroduce JWTs in
localStorage.

evidence:
docs/security-review.md and commit <sha>
```

The dashboard lights up:

```text
CODEX -> candidate decision captured
```

Approve it, or let the prepared demo show it already approved and promoted.

### Act 2 — RecallOps verifies and improves

The dashboard shows:

- the active cookie-session claim;
- the stale JWT/localStorage claim;
- source agent and session;
- source files/references returned by Cognee;
- the `CONTRADICTS` / `SUPERSEDES` relationship.

Approve the current claim, mark the stale claim superseded, attach feedback,
and run `improve(dataset=..., session_ids=[...])`.

The dashboard must show the actual Cognee operation and the resulting memory
delta. The approval button is not allowed to be cosmetic.

### Act 3 — OpenCode remembers

Start a completely fresh OpenCode session in the same repository:

```text
Add logout behavior. Do not inspect the whole repository first; use available
project memory.
```

OpenCode calls `recallops_recall` or receives automatic context:

```text
Current auth decision:
Use HTTP-only cookie sessions; never persist JWTs in localStorage.
Learned by Codex, supported by docs/security-review.md.
```

OpenCode implements the correct logout behavior without repeating the stale
approach.

The dashboard shows:

```text
CODEX -> learned decision
OPENCode <- recalled decision
OPENCode -> used in logout task
```

This is the core payoff. Stop here if the demo clock or connectivity is bad.

### Act 4 — Fresh proof and forgetting

Start another clean Codex or OpenCode session:

```text
What must every future auth change preserve?
```

It returns the durable corrected rule with references and does not return the
superseded rule as current truth.

Then delete one seeded disposable/private test memory with `forget()` and run a
follow-up recall proving that it is absent.

### Act 5 — Hermes remembers (optional stretch)

Only if the core demo is already reliable, start a fresh Hermes session backed
by the official Cognee memory provider:

```text
Before editing authentication, what project constraints must I preserve?
```

Hermes recalls the same active decision from the shared project dataset. This
proves integration breadth without inventing a third adapter.

Close with the product line:

> Codex learned it. RecallOps verified it. OpenCode used it. Cognee made it
> durable.

## Dashboard

The landing view must explain the product without narration.

### Hero

```text
Trusted shared memory for every coding agent

2 agents connected · 12 durable memories · 1 conflict to review
```

### Main visualization: agent relay

A horizontal swimlane is clearer than a generic graph:

```text
Codex          RecallOps / Cognee          OpenCode
  learned  ─────────►  reviewed  ─────────► recalled
                         │                      │
                         └── improved graph ◄───┘
```

Use recognizable agent names/colors and animate only the latest event.

### Memory cards

Each card shows:

- type;
- concise statement;
- permanent or session-only;
- originating agent and session;
- evidence;
- last recalled by;
- confidence/approval state.

### Review inbox

Side-by-side current and proposed memories with:

- approve;
- edit;
- supersede;
- reject;
- forget.

### Cognee inspector

A compact drawer, not the primary screen:

- session id;
- dataset;
- source (`session` or `graph`);
- retrieval path/strategy if available;
- source references returned by Cognee;
- pipeline status;
- graph visualization link.

This makes the Cognee usage technically inspectable without forcing judges to
read a graph.

## Demo timing

Target: 2 minutes 40 seconds.

```text
0:00–0:15  Problem and promise: "Switch agents, not project truth."
0:15–0:45  Codex records the current auth decision with evidence.
0:45–1:15  RecallOps exposes the stale conflict and source references.
1:15–1:40  Approve, supersede, and run Cognee improve.
1:40–2:15  Fresh OpenCode recalls and applies the corrected rule.
2:15–2:30  Before/after result and graph-memory delta.
2:30–2:40  Forget proof and close.
```

Keep a pre-seeded state and a one-click demo reset. Record a fallback video of
the complete flow. Do not perform package installation, indexing, or a long
Cognee pipeline live.

## What is real versus staged

Real:

- two independently authenticated agent CLIs;
- shared Cognee dataset;
- unique session ids and source-agent attribution;
- actual recall in a fresh agent;
- actual session-to-graph promotion;
- actual dashboard event stream;
- actual evidence files;
- actual Cognee references via `include_references=True`;
- actual forget operation if shown.

Prepared for reliability:

- tiny repository and deterministic task;
- seeded old and current design notes;
- pre-indexed graph;
- short tests;
- optional prepared candidate conflict;
- reset script.

Never fake tool success or show hard-coded "recalled" text.

## Subscription and model boundary

Codex and OpenCode continue to use the user's existing ChatGPT subscription
authentication. RecallOps does not need an OpenAI API key to operate those
agents. Optional Hermes can use its `openai-codex` OAuth provider.

Cognee still needs a configured extraction/embedding path:

- Cloud track: use the hackathon Cognee Cloud tenant/credit.
- Local fallback: use local Cognee with a small Ollama model plus Fastembed, or a
  free supported provider during the demo.

Do not build a proxy that converts Codex subscription access into a fake
OpenAI-compatible API for Cognee. It adds fragility and distracts from the
product.

## Submission track

The kickoff says one project should not be entered into two tracks. RecallOps
will target the **Cognee Cloud application track** because shared team memory
across agents and machines is its strongest product story.

Cloud proof:

- Codex and OpenCode connect to one Cloud project dataset;
- session memory is isolated per run;
- permanent graph is shared;
- dashboard shows connected agents and activity;
- fresh agent/machine recalls prior work.

Local Cognee remains the development and deterministic fallback mode. Do not
submit the same RecallOps project separately as an OSS-track application. The
open-source bounty/PR track is a separate effort and is out of scope unless the
main product is finished and an issue is formally assigned.

## Why this maximizes Cognee

Removing Cognee destroys every important property:

- no cross-agent persistent memory;
- no session-to-permanent distillation;
- no graph of decisions, failures, and evidence;
- no semantic/graph recall;
- no improve loop;
- no governed forgetting;
- no local-to-Cloud deployment story.

The app is therefore not a dashboard placed on Cognee. It is a productization
of Cognee's agent-memory lifecycle.

## MVP build order

1. One project-scoped Cognee dataset and two conflicting test memories.
2. One Cognee HTTP service; no shared embedded file-store access.
3. `recallops_recall`, `recallops_record`, and `recallops_handoff`.
4. Codex integration with visible source/session attribution.
5. OpenCode integration and successful cross-agent recall.
6. Minimal dashboard relay, memory cards, and source-reference drawer.
7. Review/supersede/feedback flow using real `improve()`.
8. Deterministic baseline-versus-improved evaluation.
9. Forget proof and graph inspector.
10. Cognee Cloud switch, then frontend polish and failure-state hardening.
11. Optional official Hermes integration.

The demo is viable when step 8 works. Hermes must not block the
Codex-to-OpenCode relay.

## Primary risks

- **Too much adapter work:** reuse Cognee's official Codex and OpenCode
  integrations; do not write a Hermes adapter.
- **Concurrent local-store access:** route all agents through one Cognee HTTP
  service; use Postgres or Cloud for the multi-agent deployment.
- **Noisy automatic memory:** promote only high-value typed candidates.
- **Slow indexing:** pre-index and never index a repository live.
- **Dashboard becomes the project:** every visible event must correspond to a
  real Cognee operation.
- **Three terminals become confusing:** use the dashboard relay as the stable
  visual anchor. The core demo uses only Codex and OpenCode.
- **Hermes scope creep:** install the official provider only after the complete
  lifecycle is stable; never turn Hermes into a second product.

## Current source evidence

- Codex MCP:
  https://developers.openai.com/codex/mcp
- Codex hooks:
  https://developers.openai.com/codex/hooks
- Cognee Codex integration:
  https://github.com/topoteretes/cognee-integrations/tree/main/integrations/codex
- Cognee OpenCode integration:
  https://github.com/topoteretes/cognee-integrations/tree/main/integrations/opencode
- Cognee Hermes Agent integration:
  https://github.com/topoteretes/cognee-integrations/tree/main/integrations/hermes-agent
- Hermes Agent:
  https://github.com/NousResearch/hermes-agent
- OpenCode MCP:
  https://opencode.ai/docs/mcp-servers
- OpenCode plugins:
  https://opencode.ai/docs/plugins
- Cognee sessions:
  https://docs.cognee.ai/core-concepts/sessions-and-caching
- Cognee Cloud:
  https://docs.cognee.ai/cognee-cloud/overview
