from __future__ import annotations

from uuid import UUID, uuid4

from returns.result import Failure, Success

from recallops.errors import AppError, AppResult, ErrorKind
from recallops.gateway import CogneeGateway
from recallops.models import (
    AgentName,
    ApproveMemoryRequest,
    ConflictRecord,
    EvidenceReference,
    HandoffPack,
    HandoffRequest,
    MemoryKind,
    MemoryRecord,
    MemoryStatus,
    OperationEvent,
    ProjectOverview,
    RecallRequest,
    RecallResult,
    RecordMemoryRequest,
    utc_now,
)
from recallops.store import SQLiteStore


class RecallOpsService:
    def __init__(self, store: SQLiteStore, gateway: CogneeGateway) -> None:
        self._store = store
        self._gateway = gateway

    def record(self, request: RecordMemoryRequest) -> AppResult[MemoryRecord]:
        memory = MemoryRecord(
            project=request.project,
            agent=request.agent,
            session_id=request.session_id,
            kind=request.kind,
            subject=request.subject,
            statement=request.statement,
            evidence=request.evidence,
            confidence=request.confidence,
            status=MemoryStatus.CANDIDATE,
        )
        cognee_result = self._gateway.remember(
            memory,
            self._dataset(request.project, "working"),
            request.session_id,
        )
        if isinstance(cognee_result, Failure):
            return Failure(cognee_result.failure())
        memory = memory.model_copy(update={"cognee_entry_id": cognee_result.unwrap()})
        saved = self._store.save_memory(memory)
        if isinstance(saved, Failure):
            return saved

        active_result = self._store.active_for_subject(request.project, request.subject)
        if isinstance(active_result, Failure):
            return Failure(active_result.failure())
        active = active_result.unwrap()
        if active is not None and active.statement != memory.statement:
            conflict = ConflictRecord(
                project=request.project,
                subject=request.subject,
                current_memory_id=active.id,
                candidate_memory_id=memory.id,
            )
            conflict_result = self._store.save_conflict(conflict)
            if isinstance(conflict_result, Failure):
                return Failure(conflict_result.failure())
            self._event(
                request.project,
                "conflict.detected",
                "Conflicting project truth detected",
                f"{request.subject} has a current memory and a new candidate.",
                request.agent,
                memory.id,
            )

        event_result = self._event(
            request.project,
            "memory.captured",
            f"{request.agent.value.title()} captured a {request.kind.value}",
            request.statement,
            request.agent,
            memory.id,
        )
        if isinstance(event_result, Failure):
            return Failure(event_result.failure())
        return Success(memory)

    def approve(
        self,
        memory_id: UUID,
        request: ApproveMemoryRequest,
        idempotency_key: str,
    ) -> AppResult[MemoryRecord]:
        prior_result = self._store.get_idempotent_resource(idempotency_key, "approve")
        if isinstance(prior_result, Failure):
            return Failure(prior_result.failure())
        prior = prior_result.unwrap()
        if prior is not None:
            prior_memory_id = UUID(prior.split(":", maxsplit=1)[-1])
            return self._store.get_memory(prior_memory_id)

        candidate_result = self._store.get_memory(memory_id)
        if isinstance(candidate_result, Failure):
            return candidate_result
        candidate = candidate_result.unwrap()
        if candidate.status is not MemoryStatus.CANDIDATE:
            return Failure(
                AppError(
                    ErrorKind.CONFLICT,
                    "Only candidate memories can be approved.",
                    {"memory_id": str(memory_id), "status": candidate.status.value},
                )
            )

        curated_session = f"recallops-approved:{candidate.project}:{uuid4()}"
        current_dataset = self._dataset(candidate.project, "current")
        cognee_result = self._gateway.remember(candidate, current_dataset, curated_session)
        if isinstance(cognee_result, Failure):
            return Failure(cognee_result.failure())
        improve_result = self._gateway.improve(current_dataset, (curated_session,))
        if isinstance(improve_result, Failure):
            return Failure(improve_result.failure())

        superseded_id = request.supersede_memory_id
        if superseded_id is not None:
            old_result = self._store.get_memory(superseded_id)
            if isinstance(old_result, Failure):
                return old_result
            old = old_result.unwrap()
            if old.project != candidate.project or old.subject != candidate.subject:
                return Failure(
                    AppError(
                        ErrorKind.CONFLICT,
                        "The superseded memory must describe the same project subject.",
                    )
                )
            archived = old.model_copy(
                update={"status": MemoryStatus.SUPERSEDED, "updated_at": utc_now()}
            )
            archive_result = self._store.save_memory(archived)
            if isinstance(archive_result, Failure):
                return archive_result

        active = candidate.model_copy(
            update={
                "status": MemoryStatus.ACTIVE,
                "supersedes_id": superseded_id,
                "cognee_entry_id": cognee_result.unwrap(),
                "session_id": curated_session,
                "updated_at": utc_now(),
            }
        )
        save_result = self._store.save_memory(active)
        if isinstance(save_result, Failure):
            return save_result

        conflicts_result = self._store.list_conflicts(candidate.project, unresolved_only=True)
        if isinstance(conflicts_result, Failure):
            return Failure(conflicts_result.failure())
        for conflict in conflicts_result.unwrap():
            if conflict.candidate_memory_id == memory_id:
                resolved = conflict.model_copy(update={"resolved": True})
                result = self._store.save_conflict(resolved)
                if isinstance(result, Failure):
                    return Failure(result.failure())

        for metric in ("improvements",):
            metric_result = self._store.increment_metric(candidate.project, metric)
            if isinstance(metric_result, Failure):
                return Failure(metric_result.failure())
        event_result = self._event(
            candidate.project,
            "memory.improved",
            "Project truth approved and improved",
            request.reason,
            None,
            active.id,
        )
        if isinstance(event_result, Failure):
            return Failure(event_result.failure())
        idempotency_result = self._store.save_idempotency(
            idempotency_key,
            "approve",
            f"{candidate.project}:{active.id}",
        )
        if isinstance(idempotency_result, Failure):
            return Failure(idempotency_result.failure())
        return Success(active)

    def recall(self, request: RecallRequest) -> AppResult[RecallResult]:
        gateway_result = self._gateway.recall(
            request.query,
            self._dataset(request.project, "current"),
        )
        if isinstance(gateway_result, Failure):
            return Failure(gateway_result.failure())
        memories_result = self._store.list_memories(request.project, (MemoryStatus.ACTIVE,))
        if isinstance(memories_result, Failure):
            return Failure(memories_result.failure())
        memories = self._relevant(memories_result.unwrap(), request.query)
        gateway_recall = gateway_result.unwrap()
        references = self._merge_references(
            gateway_recall.references,
            tuple(reference for memory in memories for reference in memory.evidence),
        )
        metric_result = self._store.increment_metric(request.project, "recalls")
        if isinstance(metric_result, Failure):
            return Failure(metric_result.failure())
        event_result = self._event(
            request.project,
            "memory.recalled",
            "Current project truth recalled",
            request.query,
            None,
            memories[0].id if memories else None,
        )
        if isinstance(event_result, Failure):
            return Failure(event_result.failure())
        return Success(
            RecallResult(
                query=request.query,
                memories=memories,
                references=references,
                source=gateway_recall.source,
            )
        )

    def handoff(self, request: HandoffRequest) -> AppResult[HandoffPack]:
        recall_result = self.recall(RecallRequest(project=request.project, query=request.goal))
        if isinstance(recall_result, Failure):
            return Failure(recall_result.failure())
        recalled = recall_result.unwrap()
        memories = recalled.memories
        pack = HandoffPack(
            project=request.project,
            goal=request.goal,
            target_agent=request.target_agent,
            decisions=tuple(m for m in memories if m.kind is MemoryKind.DECISION),
            constraints=tuple(m for m in memories if m.kind is MemoryKind.CONSTRAINT),
            failures_to_avoid=tuple(m for m in memories if m.kind is MemoryKind.FAILURE),
            open_questions=tuple(m for m in memories if m.kind is MemoryKind.QUESTION),
            references=recalled.references,
        )
        event_result = self._event(
            request.project,
            "handoff.generated",
            f"Handoff prepared for {request.target_agent.value.title()}",
            request.goal,
            request.target_agent,
            memories[0].id if memories else None,
        )
        if isinstance(event_result, Failure):
            return Failure(event_result.failure())
        return Success(pack)

    def overview(self, project: str) -> AppResult[ProjectOverview]:
        candidates = self._store.list_memories(project, (MemoryStatus.CANDIDATE,))
        active = self._store.list_memories(project, (MemoryStatus.ACTIVE,))
        conflicts = self._store.list_conflicts(project, unresolved_only=True)
        events = self._store.list_events(project)
        improvements = self._store.get_metric(project, "improvements")
        recalls = self._store.get_metric(project, "recalls")
        results = (candidates, active, conflicts, events, improvements, recalls)
        for result in results:
            if isinstance(result, Failure):
                return Failure(result.failure())
        return Success(
            ProjectOverview(
                project=project,
                memory_backend=self._gateway.mode,
                candidates=len(candidates.unwrap()),
                active_memories=len(active.unwrap()),
                conflicts=len(conflicts.unwrap()),
                improvements=improvements.unwrap(),
                recalls=recalls.unwrap(),
                events=events.unwrap(),
            )
        )

    def list_memories(self, project: str) -> AppResult[tuple[MemoryRecord, ...]]:
        return self._store.list_memories(project)

    def list_conflicts(self, project: str) -> AppResult[tuple[ConflictRecord, ...]]:
        return self._store.list_conflicts(project)

    def reset_project(self, project: str) -> AppResult[None]:
        return self._store.reset_project(project)

    def seed_demo(self, project: str) -> AppResult[MemoryRecord]:
        reset = self.reset_project(project)
        if isinstance(reset, Failure):
            return reset
        stale = MemoryRecord(
            project=project,
            agent=AgentName.DEMO,
            session_id="demo:legacy-auth",
            kind=MemoryKind.DECISION,
            subject="auth.session-strategy",
            statement="Persist JWT access tokens in localStorage for all browser sessions.",
            evidence=(
                EvidenceReference(
                    label="Legacy auth design",
                    uri="demo/auth-migration-repo/docs/legacy-auth.md",
                    excerpt="The browser stores the access token in localStorage.",
                ),
            ),
            confidence=0.72,
            status=MemoryStatus.ACTIVE,
            cognee_entry_id="demo-stale-auth",
        )
        save_result = self._store.save_memory(stale)
        if isinstance(save_result, Failure):
            return save_result
        event = self._event(
            project,
            "demo.ready",
            "Stale project memory loaded",
            "The project is ready for the Codex → OpenCode demonstration.",
            AgentName.DEMO,
            stale.id,
        )
        if isinstance(event, Failure):
            return Failure(event.failure())
        return Success(stale)

    @staticmethod
    def _dataset(project: str, stage: str) -> str:
        return f"recallops:{project}:{stage}"

    @staticmethod
    def _relevant(memories: tuple[MemoryRecord, ...], query: str) -> tuple[MemoryRecord, ...]:
        terms = {term.lower().strip(".,?!:;") for term in query.split() if len(term) > 3}
        matches = tuple(
            memory
            for memory in memories
            if not terms
            or terms.intersection(
                {word.lower().strip(".,?!:;") for word in memory.statement.split()}
                | set(memory.subject.split("."))
            )
        )
        return matches or memories

    @staticmethod
    def _merge_references(
        primary: tuple[EvidenceReference, ...],
        secondary: tuple[EvidenceReference, ...],
    ) -> tuple[EvidenceReference, ...]:
        seen: set[str] = set()
        merged: list[EvidenceReference] = []
        for reference in primary + secondary:
            if reference.uri not in seen:
                seen.add(reference.uri)
                merged.append(reference)
        return tuple(merged)

    def _event(
        self,
        project: str,
        event_type: str,
        title: str,
        detail: str,
        actor: AgentName | None,
        memory_id: UUID | None,
    ) -> AppResult[OperationEvent]:
        return self._store.add_event(
            OperationEvent(
                project=project,
                type=event_type,
                title=title,
                detail=detail,
                actor=actor,
                memory_id=memory_id,
            )
        )
