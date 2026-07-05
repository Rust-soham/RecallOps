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

## Quick start

Requirements:

- Python 3.12;
- [`uv`](https://docs.astral.sh/uv/);
- Linux Node.js 20+ for rebuilding the dashboard.

```bash
uv sync --dev
npm --prefix web install
npm --prefix web run build
uv run recallops-seed
uv run recallops-api
```

Open [http://127.0.0.1:8787](http://127.0.0.1:8787). The API serves the built
dashboard directly, so Node is not needed after the build.

The default is explicitly labeled **Demo memory adapter**. It never pretends to
be Cognee. To use a local or Cloud Cognee service:

```bash
cp .env.example .env
# Set RECALLOPS_COGNEE_MODE=http, API Base URL, API key, and Tenant ID.
uv run recallops-api
```

RecallOps targets Cognee's current HTTP surface:

- `POST /api/v1/remember`
- `POST /api/v1/recall` with references enabled
- `POST /api/v1/improve` when available

Cognee Cloud's synchronous `remember` route automatically bridges session
memory into the graph. RecallOps therefore treats a missing Cloud `improve`
route as successful automatic improvement rather than redundantly running
`cognify`.

## Agent setup

The repository includes project-local configuration for both agents:

- Codex: `.codex/config.toml`
- OpenCode: `opencode.json`

OpenCode can verify the connection with:

```bash
opencode mcp list
```

Codex loads project MCP configuration only for trusted projects. If the
project-local server does not appear in `/mcp`, add it explicitly:

```bash
codex mcp add recallops -- /home/soham/.local/bin/uv run recallops-mcp
```

The MCP server exposes only:

- `recallops_record`
- `recallops_recall`
- `recallops_handoff`

`AGENTS.md` tells both clients when memory is worth recording and forbids
secrets or transient exhaust.

## Canonical demo

1. Reset the dashboard. This loads the stale JWT/localStorage decision.
2. Ask Codex to inspect `demo/auth-migration-repo` and record the approved
   authentication decision with evidence.
3. In RecallOps, compare the stale and proposed claims, inspect provenance, and
   click **Approve & supersede**.
4. Start a fresh OpenCode session and ask it to use `recallops_handoff` before
   implementing secure logout.
5. Run the fixture test. The starting implementation intentionally fails; the
   correct solution clears the cookie and revokes the refresh session.

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
