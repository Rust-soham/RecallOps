# Reference repo sweep — Cognee hackathon

Initial sweep: 2026-06-29. Cognee integrations and Hermes Agent were refreshed
on 2026-06-30 after the kickoff transcript named Hermes explicitly.

Important framing: the Coral repos below are only a presentation/quality bar from the previous hackathon. The implementation reference for this project is the Cognee ecosystem itself. For the Cognee-only build map, use `COGNEE_EXAMPLES_MAP.md`.

## Repos checked

| Repo | Commit checked | Why it matters |
| --- | --- | --- |
| [yashhh-23/coral-powered-optimizer](https://github.com/yashhh-23/coral-powered-optimizer) | `da20b511bb82bdfdcab478e5a75312cee2f911a0` — 2026-05-31 | Prior Coral winner/reference: small but deployed, visible sponsor-tech demo. |
| [akash-mondal/manthan](https://github.com/akash-mondal/manthan) | `b84c055df6aef1d585c38e64fd288aae1134b150` — 2026-06-09 | Prior Coral winner/reference: very polished product narrative, citations, live trace, action cinematic. |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | `1913271821c84cec1630dd5b15ceb17dee8ace55` — 2026-06-26 | Core Cognee platform: current public README/API/examples. GitHub API showed the repo was pushed again on 2026-06-29. |
| [topoteretes/cognee-integrations](https://github.com/topoteretes/cognee-integrations) | `a7bfebbdd46098e0fd81d88f45794f939cfc5b38` — 2026-06-27 | Directly relevant: Codex, OpenCode, Claude Code, OpenClaw, LangGraph, CrewAI, n8n integrations. GitHub API showed it was pushed again on 2026-06-29. |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | `05ac16778bda321bd4726c17bd7061b110255582` — 2026-06-29 | Optional real third agent. Supports ChatGPT/Codex OAuth; use Cognee's official provider rather than building an adapter. |
| [topoteretes/cognee-hackathons](https://github.com/topoteretes/cognee-hackathons) | `746a8da1a6a801061365e0dfdf0ef15079a64f78` — 2026-06-26 | Hackathon grammar/templates: Company Brain, Cloud, ingest/query/self-improve/lint, submission evidence. |
| [topoteretes/cognee-rs](https://github.com/topoteretes/cognee-rs) | `37cb1e1d707fe5df9648ac025b5d3841fb229911` — 2026-06-29 | New Rust/TS/C bindings and on-device memory direction. Not v1-critical, but useful for positioning. |
| [topoteretes/cognee-community](https://github.com/topoteretes/cognee-community) | `52281288052970f57e533b9be75b64da9ac7c773` — 2026-06-24 | Adapters/custom pipelines/community examples. |
| [topoteretes/karpathy-wiki](https://github.com/topoteretes/karpathy-wiki) | `58d1d77d1c4fc84b34aab78688e67dc724f755e7` — 2026-05-31 | Concrete “LLM wiki / living brain” example with markdown artifact + Cognee-backed query/improve/lint loop. |
| [topoteretes/awesome-ai-memory](https://github.com/topoteretes/awesome-ai-memory) | `331be5d6a630412d07ec421bad18f5b333f77e1f` — 2026-06-18 | Positioning landscape and competitor warning. |
| [Felo-Inc/memclaw](https://github.com/Felo-Inc/memclaw) | `9aeaebcdbaff477090ac2931ae61ebad7f98e7e5` — 2026-04-23 | Competitor/reference: project-isolated memory for AI coding agents with dashboard. Avoid looking like a generic clone. |

## Important updates / ecosystem signals

- The Cognee org is active during the hackathon window. GitHub API showed `topoteretes/cognee` and `topoteretes/cognee-integrations` had 2026-06-29 pushes.
- `cognee-integrations` contains integrations for `codex`, `opencode`, and
  `hermes-agent`. This changes the RecallOps build plan: reuse official memory
  capture rather than building adapters from scratch.
- `cognee-rs` is new and active. It pitches fast on-device AI memory, Rust CLI, TypeScript bindings, session memory, memify, improve, and visualization. This is not the v1 base, but it is useful for “future local devtool memory” positioning.
- Cognee’s own hackathon materials repeatedly frame the winning loop as: session scratchpad → durable graph → recall across sessions → feedback/self-improvement → lint/conflict/staleness control.
- The kickoff independently validated the product: Cognee described coding
  agents sharing captured conversation knowledge across teams and confirmed
  source references for debugging wrong answers.

## Presentation bar only: what the Coral winners teach

### `coral-powered-optimizer`

What to steal:

- Clear target user: GSoC/open-source aspirants.
- Sponsor tech is obvious: Coral joins LeetCode + GitHub through SQL/MCP.
- Frontend exists and explains the backend: chat UI, schema explorer, quick prompts, visible SQL metadata.
- README is demo-ready: problem, solution, core features, architecture, deployment links, local setup.

Implication:

- Even if the backend idea is strong, judges need a quick visual loop. For RecallOps, the equivalent is not a generic graph; it is a visible “agent memory handoff” timeline.

### `manthan`

What to steal:

- One canonical demo case: a chargeback resolved through investigation, cited brief, and human-approved actions.
- Sponsor tech is cinematic and legible: raw SQL feed, source chips, citations, investigation stream.
- README sells like a product landing page, not just a repo.
- It makes trust visible: every claim has a citation; every action has audit/status/external ref.
- “Memory”/history is productized as a page: what the agent remembers per customer.

Implication:

- RecallOps needs one canonical broken-context story, not a menu of features.
- The visual surface must answer: what did the agent remember, where did it learn it, which future agent used it, and what changed after feedback?

## Cognee references that map directly to RecallOps

### Core Cognee API

Relevant surface from `topoteretes/cognee`:

- `remember(...)` without `session_id`: durable graph memory.
- `remember(..., session_id=...)`: fast session memory / scratchpad.
- `recall(..., session_id=...)`: session-first recall, then graph fallback.
- `recall(..., include_references=True)`: completion results include
  source/provenance references. This is mandatory for the RecallOps inspector.
- `improve(dataset=..., session_ids=[...])`: bridge/distill session content into graph.
- `forget(...)`: deletion by dataset/item/everything.
- MCP server exposes focused `remember`, `recall`, `forget`, plus workspace UI tools such as graph visualization.
- Cloud route: `await cognee.serve(url=..., api_key=...)`; local-first can later `push(...)` to Cloud.

### Official Codex integration

Path: `/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/codex`

Key behavior:

- Captures prompts, tool traces, and assistant responses into session memory.
- Injects relevant context on `UserPromptSubmit`.
- Syncs session memory into graph memory on session end/final exit.
- Uses hooks: `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `PreCompact`, `SessionEnd`.
- Default dataset is `agent_sessions`; configurable via `COGNEE_PLUGIN_DATASET`.
- Supports Cloud/remote via `COGNEE_BASE_URL` + `COGNEE_API_KEY`, or local bootstrapped Cognee.
- Writes useful state/logs under `~/.cognee-plugin/codex/`, including hook logs, recall audit logs, statusline state, and session mapping.

RecallOps implication:

- v1 should not start by writing a full Codex adapter. Start by installing/using this and build a dashboard around its session/recall/audit state.
- The dashboard can show “saved last turn” and recall counts by reading plugin state while using Cognee API for actual memory.

### Official OpenCode integration

Path: `/tmp/cognee-reference-2026-06-29/cognee-integrations/integrations/opencode`

Key behavior:

- Package name: `@cognee/cognee-opencode`.
- Auto-captures completed tool executions through `tool.execute.after`.
- Auto-recalls into compaction through `experimental.session.compacting`.
- Improves on `session.idle`.
- Exposes custom tools:
  - `cognee_remember`
  - `cognee_search`
- Defaults to `opencode_sessions`; can share memory by setting `COGNEE_PLUGIN_DATASET`.

RecallOps implication:

- For the cross-agent demo, make Codex and OpenCode point at the same project dataset. The product proof is: Codex learns a project rule, OpenCode recalls and uses it in a fresh session.

### Hermes Agent integration

Path:
`cognee-integrations/integrations/hermes-agent`

Key behavior:

- Package: `cognee-integration-hermes-agent`.
- Stores each completed Hermes turn in Cognee session memory.
- Uses session-first recall with graph fallback.
- Exposes remember and forget.
- Runs `improve()` when a session ends.
- Supports one local Cognee server, remote/Cloud, and explicit single-process
  embedded mode.
- Its README warns against sharing local file stores across background threads
  or processes and defaults to a server for serialization.
- Hermes itself supports an `openai-codex` provider through ChatGPT/Codex
  OAuth.

RecallOps implication:

- Hermes is feasible without another paid model API and without writing an
  adapter.
- It is still stretch: the two-agent Codex → OpenCode proof, provenance,
  correction, evaluation, and polish come first.
- Do not use “Hermes” as the name of a RecallOps handoff feature.

### Claude Code integration

Even though the user does not plan to rely on Claude Code, the Claude integration is a good reference because it is the richest current lifecycle implementation:

- Background remember polling.
- Session-to-graph sync.
- Statusline.
- Skill commands.
- “Cognee preferred memory” steering.
- Auto-clear demo hook for proving memory survives transcript clearing.

RecallOps implication:

- If we need a reference for UX/status/debugging, copy the Claude/Codex plugin’s statusline and audit-log approach.

### Hackathon template

Path: `/tmp/cognee-reference-2026-06-29/cognee-hackathons/cognee-cloud-hackathon-2026-06-19`

Judging grammar:

- Three operations:
  1. Ingest
  2. Query + Self-improve
  3. Lint
- Required proof:
  - baseline run
  - improved run
  - score/feedback
  - what changed in the brain
- Architecture must explain the two-tier split:
  - session memory with `session_id`
  - permanent graph with no `session_id`
- Cloud bonus:
  - connect using `cognee.serve(...)`, or build locally and `push(...)`.

RecallOps mapping:

- Ingest: agent hooks capture prompts/tool traces/assistant responses.
- Query + self-improve: next agent recalls prior facts; feedback or review promotes corrected facts into graph.
- Lint: detect duplicates/conflicts/stale project rules, mark superseded, forget rejected memory.
- Cloud: same context ledger follows agents/machines when backed by Cognee Cloud.

## Core examples to mine

Use these as implementation references:

- `cognee/examples/demos/remember_recall_improve_example.py`
  - Cleanest top-level flow: permanent memory, session memory, `improve`, recall after enrichment.
- `cognee/examples/demos/session_flow_stepwise_demo.py`
  - Narrated trace of session guidance absorbed and distilled into permanent graph.
- `cognee/examples/demos/session_distillation_demo.py`
  - Strong proof of session scratchpad → distilled lesson docs → fresh-session recall.
- `cognee/examples/demos/session_feedback_example.py`
  - `get_session`, `add_feedback`, `delete_feedback`.
- `cognee/examples/custom_pipelines/memify_coding_agent_rule_extraction_example.py`
  - Best direct coding-agent reference: extracts coding rules from conversations into a `coding_agent_rules` node set.
- `cognee/examples/python/memory_provenance_demo.py`
  - Best visual reference for “who/what/agent/session/dataset/data/memory node provenance.”
- `cognee/examples/demos/truth_centroid_slots_demo.py`
  - Advanced reference for accepted learnings changing retrieval/ranking.
- `karpathy-wiki/scripts/wiki_common.py`
  - Good fallback pattern: markdown artifact plus Cognee optional memory; filesystem session events; works even when model/provider access is limited.
- `cognee-hackathons/cognee-cloud-hackathon-2026-06-19/templates/SUBMISSION.md`
  - Use as final submission checklist.

## Competitor / positioning warning

`Felo-Inc/memclaw` already pitches:

> “Persistent project memory for AI coding agents — isolated workspaces, visual dashboard, team collaboration.”

So RecallOps should not be framed as simply “a dashboard for coding-agent memory.”

Sharper positioning:

- “A memory flight recorder and handoff layer for AI coding agents.”
- “See what each agent learned, why it believes it, and push the corrected truth into the next agent.”
- “Cognee turns agent traces into durable project knowledge.”

Differentiators to make visible:

- Uses Cognee’s session/permanent graph split, not just a README or vector store.
- Shows provenance: fact ← session ← agent ← tool/file/evidence.
- Shows lifecycle: captured → recalled → corrected → improved/promoted → reused.
- Shows conflict/lint/forget: stale memories do not silently poison future agents.
- Cross-agent handoff is explicit: Codex → OpenCode → fresh session, with
  optional Hermes only after the core proof works.

## Recommended RecallOps demo after this sweep

One-liner:

> See what coding agents remember, trace every belief to evidence, repair stale
> project truth, and deliver the corrected memory to the next agent.

Product shape:

- Shared Cognee memory dataset per project.
- Codex and OpenCode as the core capture/recall surfaces.
- Optional Hermes through Cognee's official memory provider.
- Dashboard as the judge-facing proof surface.

Dashboard should show:

1. Agent swimlane/timeline: Codex → review/improve → OpenCode → fresh recall.
2. Memory cards:
   - fact
   - status: session-only / promoted / superseded / rejected
   - learned by
   - evidence/source
   - used by
3. Cognee lifecycle counters:
   - prompts saved
   - traces saved
   - graph recalls
   - session recalls
   - improvements/promotions
4. Conflict/lint panel:
   - stale fact detected
   - corrected fact approved
   - old fact marked superseded/forgotten

Canonical demo:

1. Start with a tiny demo repo containing stale auth context: old notes say JWT/localStorage; current code has moved to HTTP-only cookie sessions.
2. Codex fixes/learns the migration and records: “Auth uses HTTP-only cookie sessions; do not reintroduce JWTs in localStorage.”
3. Dashboard shows the fact as session memory, then promoted into Cognee graph.
4. OpenCode opens a fresh session and implements logout correctly by recalling the Codex-learned rule.
5. RecallOps records feedback, runs `improve()`, and marks the old claim
   superseded.
6. Fresh OpenCode recalls the corrected truth with source references and
   implements the right behavior without chat history.
7. A disposable memory is forgotten and a follow-up recall proves deletion.
8. Optional: fresh Hermes recalls the same corrected constraint.

Close line:

> Codex learned it. RecallOps verified it. OpenCode used it. Cognee made it
> durable.

## Build priorities

Must-have:

1. Install/use Cognee Codex integration or equivalent hook path.
2. Store project-scoped memories in one dataset.
3. Dashboard reads Cognee memories and shows provenance/lifecycle.
4. OpenCode recalls a memory created by Codex.
5. One before/after proof: without memory the agent risks stale implementation; with Cognee recall it does the right thing.
6. Every displayed belief uses real Cognee references.
7. All agents connect through one Cognee service endpoint.

Strong additions:

1. Manual review/promotion controls.
2. Conflict/lint state: active vs superseded memory.
3. `improve()` call visible in dashboard.
4. Cognee Cloud switch via env vars.
5. Blog screenshots from the dashboard.

De-scope unless the basics are stable:

- Hermes integration before the two-agent lifecycle is stable.
- Generic MCP server for every possible agent.
- Complex graph visualization as the main UI.
- Fully automatic conflict resolution.
- Big multi-repo ingestion.

## Open questions to confirm in Discord

- Exact Wednesday, July 1 Cloud opening time and whether Cloud provides LLM
  keys or only Cognee API keys.
- Required Cognee version for this hackathon (`1.2.0.dev1`, `1.2.2.dev0`, or latest).
- Whether Cloud track requires a hosted Cloud demo or if `push(...)` proof is enough.
- Final demo length and submission format for the current WeMakeDevs event.
