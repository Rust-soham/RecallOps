# Kickoff Transcript Findings

Reviewed: 2026-06-30  
Source: `liveStreamTranscript.md`

## Verdict

The kickoff strengthens the RecallOps direction.

Cognee's team explicitly described a current use case in which conversations
from coding agents are captured and their knowledge is shared across teams
(22:54–23:46). Minutes later, they confirmed that a wrong memory-backed answer
can be traced to its original source by requesting references during retrieval
(24:54–25:49).

That is the center of RecallOps:

> Shared coding-agent memory that a team can inspect, trace, correct, improve,
> and safely hand to the next agent.

This is no longer a speculative interpretation of what Cognee might value. It
is a product layer over a workflow the team presented themselves.

## Confirmed signals and plan consequences

| Kickoff signal | Product consequence |
| --- | --- |
| Cognee is a memory layer for AI apps and agents (2:28–2:58). | Keep Cognee as the product's indispensable substrate, not an attached vector search feature. |
| Contributions may be integrations or sample applications (6:18–7:10). | A polished vertical application is valid; we do not need to turn RecallOps into a Cognee core PR. |
| Cognee already integrates with OpenCode, Hermes, and Codex (19:52–20:21). | Use official integrations. Codex and OpenCode are v1; real Hermes Agent is a stretch integration, not a dashboard persona. |
| Teams use Cognee to capture agent conversations and share knowledge across teams (22:54–23:46). | Make team handoff and governed shared memory the hero use case. |
| Retrieval can return the original source/reference (24:54–25:49). | Every recalled claim in the UI must expose provenance. Use `include_references=True`; never fabricate citations. |
| `remember()` builds memory and also supports an improvement pipeline (18:56–19:52). | Show feedback plus `improve()` changing a later fresh-session result. A static ingest/search demo is insufficient. |
| Global context, weights, and self-improvement reduce irrelevant retrieval (27:49–28:35). | Capture a before/after retrieval ranking or correctness result, not only a graph animation. |
| File-backed local stores can lock under concurrent agent threads; FastAPI plus Postgres is recommended (28:41–29:28). | Agents must talk to one Cognee HTTP service. Do not let Codex, OpenCode, and Hermes open the same local graph/vector files independently. Prefer Cloud or Postgres for the submitted multi-agent deployment. |
| Complex representations require deliberate tests and manual verification (17:47–18:56). | The strict typed Python quality gate is part of the submission story, not internal polish. |
| One project should not be entered in two tracks; two distinct projects may be submitted (24:03–24:54). | Submit RecallOps to the Cloud application track. Treat local OSS as the development/fallback mode, not a second submission of the same project. |
| Cloud access was promised for Wednesday (1:39–2:28, 26:13–26:31, 30:36–31:06). | Probe access on Wednesday, July 1, 2026. The earlier “Wednesday, July 2” note was calendar-inconsistent: July 2 is Thursday. |
| The team wants concrete builder feedback (6:18–7:10, 30:36–31:38). | Keep a reproducible Cognee feedback ledger and include honest local/Cloud integration findings in the blog and README. |

## Hermes decision

Hermes is feasible without buying another model API subscription:

- Hermes Agent supports the `openai-codex` provider through ChatGPT/Codex
  OAuth.
- Cognee ships a standalone Hermes memory provider,
  `cognee-integration-hermes-agent`.
- The provider already stores completed turns in session memory, recalls with
  graph fallback, exposes remember/forget, and runs `improve()` at session end.
- Its default local-server mode deliberately keeps Cognee behind one HTTP
  process to avoid file-database concurrency problems.

However, adding a third terminal does not improve the core proof as much as
finishing provenance, conflict repair, evaluation, and frontend polish.

Decision:

1. Ship Codex → OpenCode first.
2. Add Hermes only after the full two-agent lifecycle and dashboard are
   reliable.
3. If added, show one short fresh-session recall. Do not build a custom Hermes
   runtime or name an internal RecallOps feature “Hermes.”

## Revised product sentence

> RecallOps is the flight recorder and control plane for shared AI-agent
> memory: see what Codex and OpenCode learned, trace each belief to evidence,
> resolve stale or conflicting memories, and push the corrected truth into
> every future session.

## Revised canonical demo

1. A stale repository note says authentication uses JWTs in `localStorage`.
2. Codex discovers the current HTTP-only cookie decision and records the
   evidence into a project-scoped Cognee session.
3. RecallOps shows the candidate claim, source file, session, agent, and recall
   scope. A human promotes it and marks the stale claim superseded.
4. The backend records feedback and runs `improve()` for that session.
5. A fresh OpenCode session asks how logout should work and recalls the
   corrected rule with source references.
6. The dashboard shows the cross-agent relay and a deterministic baseline
   versus improved result.
7. Optional only: a fresh Hermes session recalls the same corrected rule.
8. A disposable test memory is forgotten and a follow-up recall proves it is
   gone.

The three-minute close:

> Codex learned it. RecallOps verified it. OpenCode used it. Cognee made it
> durable.

## Remaining questions for Discord

1. Does “one project in one track” apply exactly to the Cloud application and
   open-source application tracks described to participants?
2. What is the precise Cloud activation time on Wednesday, July 1?
3. Which Cognee version and Cloud API surface should submissions pin?
4. Is a hosted deployment required, or is a reproducible Cloud-backed demo
   sufficient?
5. What are the final video length, submission fields, and blog-track
   publishing requirements?

