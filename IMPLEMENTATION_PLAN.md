# RecallOps Implementation Plan

Status: decision-complete v1 plan after kickoff transcript review  
Primary submission: Cognee Cloud application track  
Core agents: Codex and OpenCode  
Stretch agent: Hermes Agent through Cognee's official provider

## Product contract

> RecallOps is the flight recorder and control plane for shared AI-agent
> memory: see what coding agents learned, trace every belief to evidence,
> resolve stale or conflicting memories, and deliver the corrected truth to
> the next agent.

The three-minute proof is:

```text
Codex learns a current project rule
  -> Cognee stores the session and evidence
  -> RecallOps exposes a stale conflict
  -> a human approves/supersedes and runs improve()
  -> fresh OpenCode recalls the corrected rule with references
  -> a deterministic task changes from fail to pass
  -> forget() removes a disposable memory
```

If any feature does not strengthen this proof, it is out of v1.

## System boundary

RecallOps has four parts:

1. **RecallOps API and MCP tools**
   - the explicit, deterministic path used in the demo;
   - records candidates, recalls active memory, creates handoff packs, and
     logs every operation for the dashboard.
2. **Cognee**
   - source of session memory, durable graph memory, references, feedback
     weighting, improvement, and forgetting.
3. **Official agent integrations**
   - Codex and OpenCode point at the same project dataset;
   - they provide native capture/recall behavior in addition to the explicit
     RecallOps tools.
4. **RecallOps dashboard**
   - the judge-readable control surface for provenance, conflict resolution,
     improvement, evaluation, and cross-agent relay.

Do not build a Cognee-compatible reverse proxy. It adds protocol risk and is
not needed for the proof. The explicit RecallOps tools generate the product's
auditable events; the official plugins continue talking to the shared Cognee
service.

## Deployment topology

```text
Codex RecallOps MCP ──────┐
                          ├──► RecallOps API ───► operational Postgres
OpenCode RecallOps MCP ───┘          │
                                     └──────────► one Cognee service
                                                    ▲
                                                    │
official Codex plugin ──────────────────────────────┤
official OpenCode plugin ───────────────────────────┤
official Hermes provider (stretch) ─────────────────┘
```

Rules:

- One Cognee dataset per repository/project.
- One Cognee `session_id` per agent run.
- Every process uses the same Cognee service URL.
- Never let multiple agents open the same local Cognee SQLite/Kuzu/LanceDB
  files directly.
- Local development uses one Cognee HTTP server as the single writer.
- Submission mode uses Cognee Cloud. If Cloud is unavailable during recording,
  use the same API against the local server and disclose the fallback.
- RecallOps operational state uses SQLite locally and Postgres in the hosted
  deployment. It is not a second memory system; it stores workflow/audit state.

## Repository shape

```text
recallops/
  apps/
    api/
      recallops/
        api/
        domain/
        services/
        adapters/
          cognee/
          persistence/
          telemetry/
        mcp/
      tests/
    web/
      src/
        app/
        components/
        features/
          relay/
          memories/
          conflicts/
          inspector/
          evaluation/
        lib/
      e2e/
  demo/
    auth-migration-repo/
    fixtures/
    reset/
  docs/
    architecture/
    evidence/
  Makefile
  pyproject.toml
  package.json
```

Use a monorepo so the demo, API contracts, frontend, and fixtures remain
versioned together.

## Backend foundation

Reuse the production patterns proven in
`/home/soham/projects/hasan-vod-pipeline`, not its domain code.

### Toolchain and libraries

Runtime:

- Python 3.12
- `uv`
- FastAPI + Uvicorn
- Pydantic v2
- `returns.Result`
- `structlog`
- `httpx`
- SQLAlchemy 2 + Alembic
- `psycopg` for Postgres

Development:

- Ruff
- `mypy --strict`
- pytest
- Hypothesis
- respx for typed Cognee HTTP adapter tests

Use synchronous domain/services and a bounded synchronous `httpx.Client`.
FastAPI can execute sync endpoints in its thread pool. Keep any unavoidable
Cognee SDK async use inside one adapter; do not spread `asyncio` through the
domain.

### Error contract

Define:

```text
ErrorKind:
  validation
  not_found
  conflict
  cognee_unavailable
  cognee_timeout
  cognee_malformed_response
  persistence
  unauthorized
  internal

AppError:
  kind
  safe_message
  redacted_context
  correlation_id
  optional cause

AppResult[T] = Result[T, AppError]
```

All recoverable boundaries return `AppResult`. Unexpected programmer defects
log a redacted traceback with correlation ID and remain visible as internal
failures. Never log API keys, OAuth tokens, full prompts containing secrets, or
raw private memories.

### Domain models

All API/event models are strict immutable Pydantic v2 models with
`extra="forbid"`.

- `Project`
- `AgentRun`
- `TraceEvent`
- `MemoryCandidate`
- `MemoryClaim`
- `EvidenceReference`
- `RecallEvent`
- `Conflict`
- `Resolution`
- `ImprovementRun`
- `ForgetOperation`
- `HandoffPack`
- `EvalRun`

Memory state machine:

```text
candidate ──approve──► active
    │                    │
    ├──reject──► rejected├──supersede──► superseded
    │                    │
    └──forget────────────┴──forget─────► forgotten
```

Correction and deletion are different:

- supersede preserves history and provenance;
- forget invokes actual Cognee deletion and proves absence on recall.

### Cognee gateway

Expose a small typed interface:

```text
remember_session(entry, dataset, session_id)
recall(query, dataset, session_id?, include_references=True)
add_feedback(session_id, qa_id, score, text)
improve(dataset, session_ids)
forget(selector)
health()
```

Requirements:

- bounded connect/read/write/pool timeouts;
- no silent local/Cloud fallback;
- validate every response before it reaches the domain;
- include `_source` (`session` or `graph`) and source references;
- preserve Cognee request/run IDs when available;
- retries only for idempotent reads and health checks;
- structured latency and outcome metrics, with sensitive values redacted.

### RecallOps MCP tools

Keep the public agent surface to three tools:

```text
recallops_record(
  project,
  kind,
  subject,
  statement,
  evidence[],
  confidence
)

recallops_recall(
  project,
  query,
  task?,
  session_id?
)

recallops_handoff(
  project,
  goal,
  target_agent?
)
```

`recallops_record` creates a candidate in the current Cognee session and the
operational review queue. It never silently makes a claim canonical.

`recallops_recall` returns only active claims as product guidance, but includes
superseded/conflicting claims in a separate warning section when relevant. It
always requests Cognee references.

`recallops_handoff` deterministically renders:

- goal;
- active decisions;
- constraints;
- failures to avoid;
- unresolved questions;
- evidence/references;
- generation time and target agent.

Do not require a separate LLM call to render v1 handoffs. Optional prose polish
may be added behind a feature flag after deterministic output is stable.

## Cognee memory design

Dataset:

```text
project:<stable-repository-id>
```

Sessions:

```text
codex:<run-id>
opencode:<run-id>
hermes:<run-id>  # stretch only
```

V1 uses Cognee's typed session entries/traces and the normal
session-to-graph `improve()` flow. Approved claims use a structured envelope
containing:

- stable claim ID;
- subject key;
- statement;
- kind;
- source agent/session;
- evidence identifiers;
- validity status;
- creation and approval timestamps.

The operational store is authoritative for workflow status; Cognee is
authoritative for memory and retrieval. A reconciliation service detects and
surfaces divergence.

After the end-to-end path works, add a compact Cognee DataPoint projection for
`Project`, `AgentRun`, `Claim`, and `Evidence`, with `LEARNED_IN`, `SUPPORTS`,
`CONTRADICTS`, and `SUPERSEDES` edges. Do not block v1 on a custom extraction
pipeline.

Conflict detection is deterministic in v1:

- claims share a normalized `subject`;
- their canonical values/statements disagree;
- neither is already rejected, superseded, or forgotten.

LLM-based open-domain contradiction detection is stretch.

## API surface

Read:

```text
GET /api/health
GET /api/projects/{project_id}/overview
GET /api/projects/{project_id}/events
GET /api/projects/{project_id}/memories
GET /api/projects/{project_id}/conflicts
GET /api/projects/{project_id}/evaluations/latest
GET /api/memories/{memory_id}
GET /api/memories/{memory_id}/references
GET /api/events/stream?project_id=...
```

Write:

```text
POST /api/projects/{project_id}/memories
POST /api/memories/{memory_id}/approve
POST /api/memories/{memory_id}/reject
POST /api/memories/{memory_id}/supersede
POST /api/projects/{project_id}/improvements
POST /api/projects/{project_id}/handoffs
POST /api/memories/{memory_id}/forget
POST /api/projects/{project_id}/demo/reset
```

Use server-sent events for the relay animation. WebSockets add no value to this
one-way dashboard stream.

Every mutation accepts an idempotency key. Every response includes a
correlation ID. Long-running Cognee operations return an operation resource
that the UI can poll/stream rather than holding a browser request indefinitely.

## Frontend direction

The interface should feel like an operations console for memory, not a generic
AI chat app and not a neon graph toy.

### Visual language

- graphite/ink foundation with warm off-white content surfaces;
- one electric signal color for live memory movement;
- amber for unresolved conflict, red only for destructive forget;
- large editorial typography for the core claim;
- compact monospace metadata for dataset/session/reference details;
- thin connector lines and restrained glow;
- motion communicates state transitions only.

Avoid default purple gradients, glassmorphism everywhere, giant graph hairballs,
and decorative terminal spam.

Recommended stack:

- React + TypeScript + Vite
- Tailwind CSS
- Radix primitives
- TanStack Query
- Motion
- Lucide icons
- Vitest + Testing Library
- Playwright

### One judge-facing route

The main route should communicate the product in ten seconds:

```text
Hero:
  "Your agents share memory. Now you can trust it."

Relay:
  CODEX learned ─► COGNEE improved ─► OPENCODE recalled

Primary card:
  active claim + status + source + evidence + used-by

Conflict drawer:
  stale claim versus current claim + approve/supersede

Inspector:
  dataset, session, source scope, references, operation status

Proof strip:
  baseline FAIL ─► corrected memory ─► fresh-session PASS
```

Secondary routes:

1. project overview;
2. review/conflict inbox;
3. memory detail with provenance;
4. evaluation and demo reset.

The graph is an inspector drawer or modal, never the hero.

### Required interaction states

- loading skeletons;
- empty project;
- Cognee unavailable;
- operation queued/running/succeeded/failed;
- reference unavailable;
- conflict already resolved;
- stale browser mutation/idempotent replay;
- Cloud disconnected with explicit local-demo mode;
- destructive forget confirmation and post-delete proof.

## Deterministic demo fixture

Repository facts:

- `docs/legacy-auth.md`: old JWT/localStorage design.
- `docs/security-review.md`: current HTTP-only cookie decision and rationale.
- current tests enforce cookie sessions.
- a narrow logout task produces an objective pass/fail.

Seeded claims:

1. stale: “Persist JWTs in localStorage.”
2. active candidate: “Use HTTP-only cookie sessions; never persist JWTs in
   localStorage.”
3. disposable: a clearly labeled private/demo-only memory for forget proof.

Demo reset must:

- recreate operational rows;
- recreate the dedicated demo Cognee dataset/session entries;
- verify expected baseline state;
- never touch non-demo datasets;
- be idempotent.

The baseline and improved run use the same task and fixture. The only intended
difference is the corrected memory available to the fresh agent.

## Verification

`make verify` runs:

```text
ruff format --check
ruff check
mypy --strict
pytest
frontend typecheck
frontend lint
frontend unit tests
Playwright smoke test
```

Backend tests:

- strict model parsing and unknown fields;
- state-machine transitions;
- redaction;
- Cognee timeout/unavailable/malformed response;
- `include_references=True` mapping;
- session-versus-graph source mapping;
- feedback and improvement operation lifecycle;
- conflict detection;
- idempotent mutation behavior;
- forget followed by absent recall;
- event ordering and SSE reconnect;
- reconciliation after partial failure;
- local/Cloud configuration with no silent fallback.

Property tests:

- claim state transitions never produce two active canonical claims for one
  subject;
- rejected/superseded/forgotten claims never enter a handoff as active truth;
- redaction removes configured secret/token patterns;
- handoff rendering is deterministic;
- demo reset never targets a non-demo dataset.

Frontend/E2E:

- a judge can identify source agent, active memory, evidence, target agent, and
  before/after outcome without opening a terminal;
- approving a claim visibly runs improvement;
- a fresh recall event appears in the relay;
- references open the correct inspector;
- failure states do not display fake success;
- phone and 1440px desktop layouts remain legible.

## Acceptance gates

### Gate 1 — memory lifecycle

- Codex records a session candidate.
- It appears in Cognee and RecallOps with matching IDs.
- Approval plus `improve()` creates durable fresh-session recall.

### Gate 2 — cross-agent proof

- Fresh OpenCode has no prior chat history.
- It recalls the Codex-learned active decision.
- Recall includes real source references.
- The task passes the deterministic test.

### Gate 3 — trust controls

- stale and current claims appear as a conflict;
- superseding preserves provenance;
- rejected/superseded claims do not appear as active handoff truth;
- forget removes the disposable memory and follow-up recall proves absence.

### Gate 4 — presentation

- seeded reset works twice consecutively;
- the full flow completes in under three minutes;
- every network-dependent moment has a captured fallback;
- no secret or fake event appears in UI, logs, screenshots, or video;
- `make verify` is green.

### Gate 5 — Cloud submission

- Codex and OpenCode point to the same Cloud project dataset;
- fresh-client recall works;
- deployment is reachable or the exact reproducible Cloud flow is recorded;
- local fallback uses the same contracts;
- Cloud limitations are disclosed honestly.

Hermes is allowed only after Gates 1–4 are green.

## Build order

### June 30

1. Scaffold monorepo and quality gates.
2. Implement domain models, error algebra, logging, and configuration.
3. Implement fake Cognee gateway and deterministic demo fixture.
4. Build RecallOps MCP tools and operation event log against the fake.
5. Build the frontend shell and relay with seeded data.

### July 1

1. Replace fake gateway with one local Cognee service.
2. Prove record → references → feedback → improve → fresh recall.
3. Integrate Codex and OpenCode with one dataset.
4. Probe promised Wednesday Cloud access and record any friction.

### July 2

1. Connect Cloud and preserve local fallback.
2. Finish conflict resolution, source inspector, and improvement operations.
3. Wire the real event stream into the polished relay.
4. Ask one precise Discord/check-in question with a minimal reproduction if
   blocked.

### July 3

1. Complete deterministic evaluation and forget proof.
2. Harden failure states, idempotency, reconciliation, and redaction.
3. Run the complete acceptance gates.
4. Cut any feature not used in the three-minute story.

### July 4

1. Visual polish, accessibility, responsive layout, and animation timing.
2. Clean-install verification and demo reset rehearsal.
3. Capture final screenshots, graph/reference proof, and first full video.
4. Assemble README, architecture, submission, and blog from the evidence log.

### July 5

1. Final Cloud/local smoke tests and `make verify`.
2. Record the final demo early.
3. Publish repo, deployment, blog, and disclosure of AI-assistant use.
4. Submit before 23:59 UTC.

## Scope locks

Not in v1:

- Obsidian;
- generic chat with documents;
- a custom coding-agent runtime;
- a custom Hermes adapter;
- model proxying;
- autonomous code editing inside RecallOps;
- automatic deletion of conflicting memory;
- open-domain LLM conflict detection;
- multi-repository knowledge management;
- graph visualization as the main product;
- a second submission of RecallOps to another track.

## Open items that do not block implementation

- exact Wednesday Cloud activation time;
- exact required Cognee/Cloud client version;
- hosted-demo requirement;
- final video length and submission fields;
- blog publishing destination and deadline.
