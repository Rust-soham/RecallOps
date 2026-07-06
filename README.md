# RecallOps

> Your agents share memory. RecallOps makes that memory trustworthy.

RecallOps is a memory control plane for engineering teams using multiple AI
coding agents. Codex can record a project decision, a human can inspect and
approve it, and a fresh OpenCode session can receive the corrected truth with
evidence.

This repository contains the v0 vertical slice:

- one shared MCP server for Codex and OpenCode;
- candidate capture, conflict detection, and human approval;
- deterministic current-truth handoffs;
- a typed Cognee HTTP adapter with source references;
- a deterministic adapter for development without credentials;
- a live project-memory dashboard;
- the prepared JWT-to-cookie authentication demo.

## Demo walkthrough

This is the shortest path to run and verify the full cross-agent demo. It uses
the deterministic local memory adapter, so no Cognee account or API key is
required.

### 1. Clone and install

Requirements:

- Git;
- Python 3.12 or newer;
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/);
- Node.js 20 or newer and npm;
- the [Codex CLI](https://developers.openai.com/codex/cli/) and
  [OpenCode](https://opencode.ai/docs/).

```bash
git clone https://github.com/Rust-soham/RecallOps.git
cd RecallOps
uv sync --dev
npm --prefix web install
npm --prefix web run build
```

### 2. Configure the environment

```bash
cp .env.example .env
```

No secret is required for the local demo. Confirm that `.env` contains:

```dotenv
RECALLOPS_COGNEE_MODE=demo
RECALLOPS_DATABASE_PATH=data/recallops.db
```

The remaining Cognee variables may stay empty. The dashboard will deliberately
show **Demo memory adapter**, making it clear that this run is using the
deterministic adapter.

To test against a real local or Cloud Cognee service instead, set
`RECALLOPS_COGNEE_MODE=http`, `RECALLOPS_COGNEE_BASE_URL`,
`RECALLOPS_COGNEE_API_KEY`, and `RECALLOPS_COGNEE_TENANT_ID`.

### 3. Start RecallOps and open the dashboard

Seed the known stale preference, then start the API:

```bash
uv run recallops-seed
uv run recallops-api
```

Keep that terminal running. Open the RecallOps dashboard at
[http://127.0.0.1:8787](http://127.0.0.1:8787). The initial state should show:

- project **Auth Migration**;
- **1** active project truth;
- no pending review;
- the stale rule that browser JWTs are stored in `localStorage`.

If the project is not in that state, click **Reset demo** in the bottom-left
corner. The same reset is also available from another terminal:

```bash
curl -X POST http://127.0.0.1:8787/api/projects/auth-migration/reset
```

### 4. Connect RecallOps to both agents

The checked-in `.codex/config.toml` and `opencode.json` demonstrate the MCP
configuration, but they contain the original developer's absolute paths.
Register the server using paths from your clone.

First verify OpenCode's config. In `opencode.json`, replace the `cwd` value with
the output of `pwd`, and replace the first command entry with the output of
`command -v uv`. Then run:

```bash
opencode mcp list
```

**Pass condition:** `recallops` appears as connected/enabled.

Register the same server with Codex:

```bash
codex mcp remove recallops 2>/dev/null || true
codex mcp add recallops --env RECALLOPS_COGNEE_MODE=demo \
  --env RECALLOPS_DATABASE_PATH="$(pwd)/data/recallops.db" \
  -- "$(command -v uv)" --directory "$(pwd)" run recallops-mcp
codex mcp list
```

**Pass condition:** `recallops` appears enabled. Inside an interactive Codex
session, `/mcp` should also list `recallops_record`, `recallops_recall`, and
`recallops_handoff`.

> Codex loads project-local MCP configuration only for trusted projects. If it
> asks whether to trust the repository, approve it and restart the session.

### 5. Have OpenCode propose the corrected preference

From the repository root, start a fresh OpenCode session:

```bash
opencode
```

Paste this prompt:

```text
Inspect demo/auth-migration-repo/docs/legacy-auth.md and
demo/auth-migration-repo/docs/security-review.md. Use the RecallOps MCP tool
recallops_record to record the approved authentication preference as a
candidate for project "auth-migration". Use agent "opencode", kind "decision",
subject "auth.session-strategy", and cite the security review file as concrete
evidence. Do not edit any files.
```

**Pass condition:** OpenCode calls `recallops_record`, which returns `ok: true`
and a memory with status `candidate`. The dashboard should update live to show
**Needs review**, one pending memory, and a comparison between:

- **CURRENT · STALE:** JWT access tokens in `localStorage`;
- **PROPOSED · EVIDENCED:** HTTP-only, Secure, SameSite cookie sessions, with
  no browser token persistence.

### 6. Approve the preference in RecallOps

In the dashboard's **Review inbox**, inspect the evidence and click
**Approve & supersede**.

**Pass condition:** the pending review disappears, memory health becomes
**Verified**, and **Project truth** contains the cookie-session decision. The
old `localStorage` decision is retained in history with status `superseded`;
it is no longer current truth.

### 7. Have Codex retrieve the approved preference

Quit any older Codex session so this test has no chat context, then start a
fresh one from the repository root:

```bash
codex
```

Paste this prompt:

```text
I am a fresh agent working on project "auth-migration". Before answering, call
the RecallOps MCP tool recallops_recall to retrieve the current reviewed
preference for "auth.session-strategy". Tell me which browser authentication
strategy superseded the old localStorage JWT preference, and include the
evidence source returned by RecallOps. Do not inspect the repository files.
```

**Pass condition:** Codex visibly calls `recallops_recall` and answers from the
MCP result that authentication uses an HTTP-only, Secure, SameSite cookie,
never stores access or refresh tokens in `localStorage`, and cites
`demo/auth-migration-repo/docs/security-review.md`. It must not return the old
JWT/localStorage rule as current truth.

The dashboard's **Memory activity** should now show the OpenCode record, the
human approval/supersession, and the Codex recall. This completes the demo:
one agent proposed a preference, a human reviewed it, and a fresh second agent
retrieved only the approved truth through RecallOps.

RecallOps targets Cognee's current HTTP surface:

- `POST /api/v1/remember`
- `POST /api/v1/recall` with references enabled
- `POST /api/v1/improve` when available

Cognee Cloud's synchronous `remember` route automatically bridges session
memory into the graph. RecallOps therefore treats a missing Cloud `improve`
route as successful automatic improvement rather than redundantly running
`cognify`.

The MCP server exposes only `recallops_record`, `recallops_recall`, and
`recallops_handoff`. `AGENTS.md` tells both clients when memory is worth
recording and forbids secrets or transient exhaust.

The deterministic adapter exercises the complete RecallOps workflow. A claim
that the Cognee lifecycle ran is valid only when the dashboard says
**Cognee connected** and `RECALLOPS_COGNEE_MODE=http`.

## Verification

```bash
make verify
```

The gate runs Ruff formatting/linting, strict mypy, pytest/Hypothesis, frontend
type checking, and a production frontend build.

Current backend coverage includes:

- stale-versus-current conflict creation;
- candidate approval and supersession;
- improvement and fresh-agent handoff;
- idempotent approval;
- strict schemas and secret redaction;
- Cognee references and typed timeout failures;
- public API health/reset behavior.

## Architecture

```text
Codex ─────┐
           ├── RecallOps MCP/API ── typed memory gateway
OpenCode ──┘           │                    │
                       ├── SQLite audit     ├── deterministic adapter
                       ├── SSE dashboard    └── Cognee HTTP service
                       └── review state
```

RecallOps stores workflow and audit state. Cognee remains the durable memory
backend when configured. Official Cognee agent plugins are not required for
v0, avoiding duplicate capture paths.
