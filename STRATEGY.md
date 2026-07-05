# Cognee Hackathon Strategy

Status: accepted direction after the June 30 kickoff transcript review  
Hackathon: June 29–July 5, 2026  
Submission deadline: July 5, 23:59 UTC

> Kickoff-derived decisions are recorded in `KICKOFF_FINDINGS.md`.
>
> The concrete cross-agent version of this concept is specified in
> `CONTEXT_LEDGER_DEMO.md`. That file is the current implementation candidate;
> this document retains the broader strategy and scoring rationale.
>
> Current external repo sweep and implementation references are in
> `REFERENCE_REPOS.md`.

## Winning thesis

Build the product Cognee makes possible, not a generic product with Cognee
attached.

The demo must visibly prove this loop:

```text
session experience
  -> remember
  -> recall
  -> feedback and conflict resolution
  -> improve / memify
  -> better result in a fresh session
  -> forget data on demand
```

The accepted build is **RecallOps** (the internal concept was Context Ledger):

> The flight recorder and control plane for shared AI-agent memory. See what
> Codex and OpenCode learned, trace every belief to evidence, resolve stale or
> conflicting memories, and transfer the corrected truth to every future
> session.

The software-delivery use case is the first demo because the problem is real:
work split across Codex, OpenCode, terminals, repositories, and separate
sessions loses decisions and repeats mistakes. Cognee already has agent
integrations; RecallOps is the inspection, governance, and handoff layer
above them.

The kickoff directly validated the use case: Cognee's team described capturing
coding-agent conversations and sharing that knowledge across teams
(22:54–23:46), then confirmed source-reference retrieval for debugging wrong
answers (24:54–25:49).

## Why this is the best current bet

1. **Cognee is indispensable.** Persistent session and graph memory are the
   product, rather than an invisible retrieval helper.
2. **It represents Cognee's platform ambition.** It shows shared memory across
   agents, sessions, and machines, with an operational UI.
3. **It demonstrates the complete lifecycle.** `remember`, `recall`,
   `improve`/memify, and `forget` each have a natural user-facing action.
4. **It produces an unusually strong demo.** A judge can watch an agent fail
   from stale context, correct the memory, and watch a fresh agent succeed.
5. **It addresses trust.** Persistent memory is only useful in production when
   users can inspect provenance, correct conflicts, and remove sensitive data.
6. **It is authentic.** The initial problem came from actual cross-surface
   agent work, not a manufactured hackathon persona.
7. **Cognee presented the use case itself.** The kickoff explicitly described
   cross-team knowledge sharing between coding agents, making RecallOps a
   sponsor-native productization rather than a guessed use case.

## Product loop

### Capture

- Capture prompts, relevant tool traces, outcomes, decisions, and failures into
  session memory using a `session_id`.
- Start with Codex capture and one project, then prove a fresh OpenCode recall.
  Hermes is a stretch only after that two-agent loop works.
- Avoid storing indiscriminate raw exhaust. Classify candidate memories as
  decision, constraint, assumption, failure, fix, unresolved question, or
  private/transient context.

### Distill

- At session end, show a review queue of proposed durable memories.
- Accepted or edited items become permanent graph memory.
- Use `improve(dataset=..., session_ids=[...])` to bridge approved session
  context into the durable graph.
- Keep rejected, noisy, and private observations session-only.

### Inspect and repair

- Show each durable memory with source, timestamp, originating session, and
  supporting evidence returned by Cognee with `include_references=True`.
- Detect contradictions and likely superseded decisions.
- Let a human resolve a conflict by approving the current claim and recording
  why the old claim is stale.
- Use a small domain ontology:
  `Project`, `Decision`, `Constraint`, `Assumption`, `Artifact`, `Failure`,
  `Fix`, `AgentSession`, and `Evidence`.
- Useful relations:
  `SUPPORTS`, `CONTRADICTS`, `SUPERSEDES`, `APPLIES_TO`, `CAUSED`,
  `RESOLVED_BY`, and `LEARNED_IN`.

### Recall and hand off

- Generate a focused handoff pack for a new agent session:
  current decisions, constraints, relevant failures, unresolved questions, and
  evidence links.
- Inject or copy this into a fresh session.
- The handoff is the product outcome; the graph visualization is supporting
  proof, not the whole interface.

### Forget

- Provide an explicit privacy/data-lifecycle action that deletes a selected
  session or disposable dataset.
- Do not misuse `forget()` as a vague "correction" button. Corrections should
  preserve provenance; deletion should mean deletion.

## Canonical demo

Prepare a deterministic software project with two conflicting sources:

- An older design note says the app stores JWTs in `localStorage`.
- A newer approved security decision requires HTTP-only cookie sessions.
- A first agent session follows the stale note and either fails or proposes the
  wrong implementation.

Demo sequence:

1. **Baseline:** Ask a fresh OpenCode session to implement an auth-related
   change without RecallOps context. Show it
   choosing the stale path or expressing an unresolved conflict.
2. **Evidence:** Open RecallOps. Show the two claims, their dates, sources,
   and graph relationship.
3. **Feedback:** Approve the current cookie-session decision, mark the old
   JWT/localStorage claim as
   superseded, and run the improvement/distillation step.
4. **Fresh session:** Ask the same question in a clean OpenCode session. Show
   the agent recalling the cookie-session rule, the reason for the migration,
   and Cognee-provided references.
5. **Privacy:** Delete a disposable/private session dataset and show that it no
   longer appears in recall.
6. **Score:** Show the before/after eval result, not only a success animation.

Optional only after the core flow is reliable: show Hermes Agent recalling the
same corrected memory through Cognee's official Hermes provider.

The final demo should be under three minutes even if the submission permits a
longer video. Every network-dependent step needs a pre-recorded fallback.

## Judge-facing proof

Create a small fixed evaluation set early, ideally 15–25 questions/tasks. Run:

1. stateless agent;
2. recall-only agent;
3. full lifecycle agent after feedback and improvement.

Track only metrics we can actually reproduce:

- task correctness;
- stale-decision error rate;
- unsupported-claim rate;
- evidence/provenance coverage;
- repeated-mistake rate;
- latency and approximate model cost, if instrumentation is reliable.

The strongest artifact is a concrete before/after:

```text
Before: agent chose the superseded JWT/localStorage flow; score 0/1.
Feedback: newer cookie-session security decision supersedes the old note.
Memory change: conflict resolved and session distilled.
After: fresh agent chose HTTP-only cookie sessions and cited the approved
decision; score 1/1.
```

## Frontend scope

Four polished screens are enough:

1. **Project overview** — memory health, sessions, unresolved conflicts, recent
   improvements.
2. **Session review** — timeline plus proposed memories to accept/edit/reject.
3. **Conflict inbox** — competing claims with provenance and a resolution
   action.
4. **Handoff / live demo** — the memory pack and before/after agent result.

Optional after the core works:

- graph explorer;
- optional Hermes integration;
- memory diff over time;
- dataset sharing and permissions;
- exportable handoff Markdown.

Avoid a generic chat-first UI. The differentiating interaction is memory
operations.

## Architecture direction

```text
Codex / OpenCode / optional Hermes
          |
          v
RecallOps API + event stream
          |
          v
single Cognee HTTP service
          |
     +----+------------------+
     |                       |
     v                       v
session memory          candidate review
  (session_id)          + provenance UI
     |                       |
     +----------+------------+
                v
         feedback + improve
                |
                v
Cognee permanent graph + focused ontology
          |
     +----+------------------+
     |                       |
     v                       v
conflict/provenance UI   recall + handoff pack
                             |
                             v
                       fresh agent session
```

All agents must use one Cognee HTTP service. Do not run multiple embedded
Cognee clients against the same SQLite/Kuzu/LanceDB files; the founder warned
that concurrent agent threads can lock those stores. Use a single local server
for development and Cloud/Postgres for the submitted multi-agent deployment.

Keep a thin Cognee service boundary so the backend can switch to Cognee Cloud
through `cognee.serve(...)`. Cloud is the selected submission track if it is
stable; local remains the deterministic demo fallback, not a second submission
of the same project.

## Schedule

### June 29

- Watch kickoff and ingest transcript. Completed June 30.
- Record the confirmed one-project/one-track guidance and Wednesday Cloud
  opening.
- Run the smallest local `remember()` / `recall()` / `improve()` experiment.
- Freeze the problem statement and canonical demo.

### June 30

- Incorporate kickoff findings and freeze the RecallOps scope.
- Prove session memory to permanent graph distillation.
- Define the ontology and ingest the canonical conflicting sources.
- Write the first baseline eval and capture its result.

### July 1

- Complete the backend lifecycle and deterministic demo fixtures.
- Build the four-screen frontend shell.
- Ensure the core path works without Cognee Cloud.
- Probe Cognee Cloud access as soon as the promised Wednesday opening occurs.
- Use the free Cloud credit shown on the resources page if access is active.

### July 2

- Finish the Cognee Cloud integration if access opened on July 1.
- Use the 15:00 UTC mid-hackathon check-in for one precise product/technical
  feedback exchange.
- Record setup friction, API differences, latency, and migration behavior.

Note: the kickoff repeatedly says Cloud opens Wednesday. In 2026 that is July
1, not July 2. Confirm the exact activation time in Discord.

### July 3

- Finish conflict resolution, provenance, and fresh-session handoff.
- Run the full eval matrix.
- Cut anything not used in the demo.

### July 4

- UI polish, loading/error states, responsive pass, seeded demo reset.
- Draft README, architecture graphic, blog, and submission copy.
- Record a first complete demo and repair every confusing moment.

### July 5

- Final verification on a clean setup.
- Record final demo early; do not depend on the final hour.
- Publish repo, hosted experience, blog, and social post.
- Submit before 23:59 UTC.

## Scope guardrails

- One deep integration beats five shallow integrations.
- The two-agent Codex → OpenCode relay is the MVP. Hermes is stretch.
- No generic "chat with your documents."
- No graph visualization presented as the product.
- No claimed self-improvement without a measured before/after.
- No fake citations, fake tool success, or hidden manual correction.
- No frontend feature that does not strengthen the three-minute story.
- Do not let Cloud instability block the local end-to-end demo.
- Do not pursue open-source bounty PRs unless an issue is assigned and the work
  is genuinely useful; the main build takes priority.
- Do not submit RecallOps unchanged to two tracks. The kickoff says one project
  should be entered in only one track.

## Kickoff decisions and remaining questions

Confirmed:

1. Deep lifecycle usage and integrations are rewarded.
2. A sample application/integration is a valid contribution shape.
3. Cross-team coding-agent memory is an explicit Cognee use case.
4. Source references are supported and should be used for debugging.
5. Multi-agent deployments should use a server; Postgres is the recommended
   simple production store.
6. One project should not be submitted to two tracks.

Still confirm in Discord:

1. Exact Cloud activation time and supported SDK version.
2. Whether a hosted Cloud deployment is mandatory.
3. Required submission fields, video limit, and blog deadline/location.
4. Whether official integration reuse needs any special disclosure beyond
   normal open-source attribution.

## References

- Hackathon overview: https://www.wemakedevs.org/hackathons/cognee
- Rules: https://www.wemakedevs.org/hackathons/cognee/rules
- Resources: https://www.wemakedevs.org/hackathons/cognee/resources
- Schedule: https://www.wemakedevs.org/hackathons/cognee/schedule
- Cognee: https://github.com/topoteretes/cognee
- Cognee integrations: https://github.com/topoteretes/cognee-integrations
- Cognee hackathon examples:
  https://github.com/topoteretes/cognee-hackathons
- Self-improvement quickstart:
  https://docs.cognee.ai/guides/self-improvement-quickstart
- Ontologies:
  https://docs.cognee.ai/core-concepts/further-concepts/ontologies
