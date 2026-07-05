# Blog and Evidence Track

The blog is a build artifact, not a final-night recollection. Capture evidence
while working so the final writing is mostly assembly.

Prize currently listed: Keychron mechanical keyboard worth $120.  
Working deadline: July 5, 23:59 UTC unless the kickoff says otherwise.

## Working title

**Your Agent Remembered the Wrong Thing: Building a Memory Control Plane with
Cognee**

Alternatives:

- From Context Windows to Correctable Memory
- We Gave Coding Agents Memory. Then We Had to Teach Them What to Forget.
- Beyond RAG: A Before-and-After Self-Improving Agent with Cognee

## Core argument

Giving an agent persistent memory creates a second problem: memory must be
inspectable, correctable, attributable, and deletable. RecallOps uses
Cognee's session memory and durable graph to turn raw agent experience into
reviewed team knowledge, then proves the result with a fresh-session
before/after evaluation.

## Evidence to capture every day

For each meaningful experiment, append an entry below with:

- timestamp and commit;
- hypothesis;
- exact input/data;
- exact command or UI action;
- observed result;
- screenshot/video path;
- latency/cost if available;
- what failed or surprised us;
- product or API feedback for Cognee;
- whether the result is safe to claim publicly.

Do not record secrets, API keys, private Discord messages, or personal data.

## Build log

### 2026-06-29 — Strategy and research

Hypothesis:

> A visible memory-quality loop will score better than a generic assistant
> because the published rules reward deep use of the entire Cognee lifecycle.

Evidence:

- Judging has six dimensions: impact, innovation, technical excellence, best
  use of Cognee, user experience, and presentation.
- Rules explicitly say deeper use of `remember`, `recall`, `improve`/memify,
  `forget`, and integrations scores more strongly.
- Cognee's recent Cloud hackathon template asks for a baseline, recorded
  feedback, a visible memory change, and an improved run.
- Previous Coral winners made sponsor technology legible through polished,
  deployed product experiences. The current repositories are stronger public
  packages than Coral Compass's Discord-only surface, although Manthan also
  contains post-deadline commits and should not be treated as a perfect
  snapshot of judging day.

Decision:

- Accepted product: RecallOps, a memory control plane for agent teams.
- Primary demo vertical: cross-session software-agent handoff with conflicting
  architectural decisions.
- Primary track: Cognee Cloud. The local implementation is the fallback and
  development base, not a second submission of the same project.

Artifacts:

- `STRATEGY.md`
- `BLOG_TRACK.md`

Open questions:

- Exact submission format and blog deadline.
- Exact Wednesday Cloud opening time and required Cognee version.

### 2026-06-30 — Kickoff transcript review

Hypothesis:

> RecallOps matches a use case Cognee itself wants to enable, and provenance
> plus memory correction should be the product rather than dashboard garnish.

Evidence:

- At 22:54–23:46, Cognee's team described coding-agent conversations being
  captured and their knowledge shared across teams.
- At 24:54–25:49, the founder confirmed that retrieval can return references
  back to the original information source. Current Cognee exposes this as
  `include_references=True`.
- At 18:56–19:52 and 27:49–28:35, the founder emphasized improvement,
  feedback weights, and global context rather than plain semantic retrieval.
- At 28:41–29:28, the founder warned that local file databases can lock when
  multiple agent threads access them and recommended a FastAPI/Postgres
  service.
- At 24:03–24:54, the organizers said one project should not be submitted to
  two tracks.
- The kickoff explicitly named OpenCode, Hermes, and Codex integrations.
- The current official Hermes integration already supports session memory,
  recall, remember, forget, and session-end `improve()`. Hermes Agent supports
  ChatGPT/Codex OAuth, so no additional model subscription is required.

Decisions:

- Keep RecallOps. The kickoff validates its exact problem.
- v1 is Codex → RecallOps/Cognee → fresh OpenCode.
- Make source references and conflict correction mandatory.
- Route every agent through one Cognee HTTP service.
- Submit to the Cloud application track; keep local mode as fallback.
- Hermes is a real optional third agent, not a feature/persona and not a custom
  adapter.

Artifacts:

- `liveStreamTranscript.md`
- `KICKOFF_FINDINGS.md`
- revised `STRATEGY.md`
- revised `CONTEXT_LEDGER_DEMO.md`

Open questions:

- Exact Cloud activation time on Wednesday, July 1.
- Hosted-demo and submission-video requirements.
- Blog publishing location and deadline.

## Planned article outline

1. **The failure**
   - A new agent session repeats an old mistake because the relevant decision
     lived in another context window.
2. **Memory is not the same as more context**
   - Raw transcripts are noisy.
   - Durable memory needs structure, provenance, and lifecycle controls.
3. **Why Cognee**
   - session memory;
   - hybrid graph-vector durable memory;
   - graph relationships and ontology;
   - `improve()`/memify;
   - `forget()`;
   - local-first and Cloud deployment.
4. **Architecture**
   - capture;
   - candidate memory review;
   - distillation;
   - conflict resolution;
   - focused recall and handoff.
5. **The baseline**
   - dataset and task;
   - wrong/stale answer;
   - measured score.
6. **The improvement**
   - feedback;
   - memory/graph change;
   - fresh-session result;
   - measured score.
7. **What broke**
   - honest setup and API friction;
   - false starts;
   - local versus Cloud differences.
8. **What this taught us about production agent memory**
   - retention policy;
   - human review;
   - temporal truth;
   - evaluation.
9. **Reproduce it**
   - minimal commands;
   - sample data;
   - link to live demo and repository.

## Required visuals

- Hero image: before and after sessions connected by the corrected memory.
- Architecture diagram.
- Conflict inbox screenshot.
- Session-to-permanent-memory review screenshot.
- Before/after eval chart.
- Short GIF of a fresh agent receiving the handoff.
- Graph view showing `CONTRADICTS` and `SUPERSEDES`, if visually useful.

## Claims ledger

Only publish claims after they have evidence.

| Claim | Required proof | Status |
|---|---|---|
| A fresh session avoids the stale auth decision | Repeatable before/after run | Not tested |
| `improve()` promotes reviewed session context | Cognee output/log plus recall test | Not tested |
| Conflict resolution improves task correctness | Fixed eval set and scores | Not tested |
| Cloud shares memory across sessions/machines | Two-client Cloud demo | Probe Wednesday, July 1 |
| Selected data can be forgotten | Recall test before and after deletion | Not tested |
| Ontology improves graph consistency | A/B graph or extraction comparison | Optional / not tested |
| Each active claim traces to its source | `include_references=True` output shown in UI | Not tested |
| Multi-agent access avoids shared-file locking | Both clients use one service endpoint | Not tested |

## Cognee feedback ledger

Capture feedback in this shape:

```text
Area:
Cognee version / local or Cloud:
Expected:
Observed:
Minimal reproduction:
Impact on builder:
Workaround:
Suggested improvement:
Public issue or Discord link, if shared:
```

High-value feedback is specific, reproducible, and tied to the product
workflow. Do not manufacture issues for visibility.

## Final publishing checklist

- [ ] Technical claims match reproducible results.
- [ ] All screenshots use the final UI and contain no secrets.
- [ ] Cognee is central in the title, architecture, and before/after.
- [ ] Code snippets run against the submitted version.
- [ ] Honest limitations are included.
- [ ] Repository, live demo, and video links work in a logged-out browser.
- [ ] AI-assistant usage is disclosed as required by the rules.
- [ ] Cognee and WeMakeDevs are tagged in the social post.
- [ ] Blog submission location and deadline are confirmed.
