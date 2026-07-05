from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


Statement = Annotated[str, Field(min_length=3, max_length=2000)]
Subject = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._:-]{1,127}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MemoryKind(StrEnum):
    DECISION = "decision"
    CONSTRAINT = "constraint"
    FAILURE = "failure"
    FIX = "fix"
    ASSUMPTION = "assumption"
    QUESTION = "question"


class MemoryStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    FORGOTTEN = "forgotten"


class OperationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AgentName(StrEnum):
    CODEX = "codex"
    OPENCODE = "opencode"
    DEMO = "demo"


class EvidenceReference(StrictModel):
    label: str = Field(min_length=1, max_length=240)
    uri: str = Field(min_length=1, max_length=2000)
    excerpt: str = Field(default="", max_length=1000)


class RecordMemoryRequest(StrictModel):
    project: str = Field(min_length=2, max_length=100)
    agent: AgentName
    session_id: str = Field(min_length=3, max_length=200)
    kind: MemoryKind
    subject: Subject
    statement: Statement
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1, max_length=10)
    confidence: float = Field(ge=0.0, le=1.0)


class MemoryRecord(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    project: str
    agent: AgentName
    session_id: str
    kind: MemoryKind
    subject: Subject
    statement: Statement
    evidence: tuple[EvidenceReference, ...]
    confidence: float
    status: MemoryStatus
    cognee_entry_id: str | None = None
    supersedes_id: UUID | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ConflictRecord(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    project: str
    subject: Subject
    current_memory_id: UUID
    candidate_memory_id: UUID
    resolved: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class OperationEvent(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    project: str
    type: str
    title: str
    detail: str
    actor: AgentName | None = None
    memory_id: UUID | None = None
    status: OperationStatus = OperationStatus.SUCCEEDED
    created_at: datetime = Field(default_factory=utc_now)


class ApproveMemoryRequest(StrictModel):
    supersede_memory_id: UUID | None = None
    reason: str = Field(min_length=3, max_length=500)


class RecallRequest(StrictModel):
    project: str = Field(min_length=2, max_length=100)
    query: str = Field(min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, max_length=200)


class RecallResult(StrictModel):
    query: str
    memories: tuple[MemoryRecord, ...]
    references: tuple[EvidenceReference, ...]
    source: str


class GatewayRecall(StrictModel):
    entry_ids: tuple[str, ...] = ()
    references: tuple[EvidenceReference, ...] = ()
    source: str = "graph"


class HandoffRequest(StrictModel):
    project: str = Field(min_length=2, max_length=100)
    goal: str = Field(min_length=3, max_length=1000)
    target_agent: AgentName = AgentName.OPENCODE


class HandoffPack(StrictModel):
    project: str
    goal: str
    target_agent: AgentName
    decisions: tuple[MemoryRecord, ...]
    constraints: tuple[MemoryRecord, ...]
    failures_to_avoid: tuple[MemoryRecord, ...]
    open_questions: tuple[MemoryRecord, ...]
    references: tuple[EvidenceReference, ...]
    generated_at: datetime = Field(default_factory=utc_now)


class ProjectOverview(StrictModel):
    project: str
    memory_backend: str
    candidates: int
    active_memories: int
    conflicts: int
    improvements: int
    recalls: int
    events: tuple[OperationEvent, ...]
