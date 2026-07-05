from pathlib import Path

from returns.result import Failure, Success

from recallops.gateway import DemoCogneeGateway
from recallops.models import (
    AgentName,
    ApproveMemoryRequest,
    EvidenceReference,
    HandoffRequest,
    MemoryKind,
    MemoryStatus,
    RecordMemoryRequest,
)
from recallops.service import RecallOpsService
from recallops.store import SQLiteStore


def build_service(path: Path) -> RecallOpsService:
    store = SQLiteStore(path)
    assert isinstance(store.initialize(), Success)
    return RecallOpsService(store, DemoCogneeGateway())


def candidate_request(project: str = "auth-migration") -> RecordMemoryRequest:
    return RecordMemoryRequest(
        project=project,
        agent=AgentName.CODEX,
        session_id="codex:test-session",
        kind=MemoryKind.DECISION,
        subject="auth.session-strategy",
        statement=("Use HTTP-only cookie sessions and never persist JWTs in browser localStorage."),
        evidence=(
            EvidenceReference(
                label="Security review",
                uri="demo/auth-migration-repo/docs/security-review.md",
                excerpt="Browser authentication uses an HTTP-only cookie.",
            ),
        ),
        confidence=0.98,
    )


def test_cross_agent_memory_lifecycle(tmp_path: Path) -> None:
    service = build_service(tmp_path / "recallops.db")
    stale_result = service.seed_demo("auth-migration")
    assert isinstance(stale_result, Success)
    stale = stale_result.unwrap()

    candidate_result = service.record(candidate_request())
    assert isinstance(candidate_result, Success)
    candidate = candidate_result.unwrap()
    assert candidate.status is MemoryStatus.CANDIDATE

    conflicts_result = service.list_conflicts("auth-migration")
    assert isinstance(conflicts_result, Success)
    conflicts = conflicts_result.unwrap()
    assert len(conflicts) == 1
    assert conflicts[0].current_memory_id == stale.id

    approved_result = service.approve(
        candidate.id,
        ApproveMemoryRequest(
            supersede_memory_id=stale.id,
            reason="The approved security review supersedes the legacy design.",
        ),
        "approve-auth-v1",
    )
    assert isinstance(approved_result, Success)
    approved = approved_result.unwrap()
    assert approved.status is MemoryStatus.ACTIVE
    assert approved.supersedes_id == stale.id

    handoff_result = service.handoff(
        HandoffRequest(
            project="auth-migration",
            goal="Implement secure logout behavior.",
            target_agent=AgentName.OPENCODE,
        )
    )
    assert isinstance(handoff_result, Success)
    handoff = handoff_result.unwrap()
    assert handoff.target_agent is AgentName.OPENCODE
    assert [memory.id for memory in handoff.decisions] == [candidate.id]
    assert stale.id not in [memory.id for memory in handoff.decisions]
    assert handoff.references[0].uri.endswith("security-review.md")

    overview_result = service.overview("auth-migration")
    assert isinstance(overview_result, Success)
    overview = overview_result.unwrap()
    assert overview.conflicts == 0
    assert overview.improvements == 1
    assert overview.recalls == 1


def test_approval_is_idempotent(tmp_path: Path) -> None:
    service = build_service(tmp_path / "recallops.db")
    stale_result = service.seed_demo("auth-migration")
    candidate_result = service.record(candidate_request())
    assert isinstance(stale_result, Success)
    assert isinstance(candidate_result, Success)
    request = ApproveMemoryRequest(
        supersede_memory_id=stale_result.unwrap().id,
        reason="Approved security review.",
    )
    first = service.approve(candidate_result.unwrap().id, request, "same-key")
    second = service.approve(candidate_result.unwrap().id, request, "same-key")
    assert isinstance(first, Success)
    assert isinstance(second, Success)
    assert first.unwrap().id == second.unwrap().id


def test_cannot_approve_active_memory(tmp_path: Path) -> None:
    service = build_service(tmp_path / "recallops.db")
    stale_result = service.seed_demo("auth-migration")
    assert isinstance(stale_result, Success)
    result = service.approve(
        stale_result.unwrap().id,
        ApproveMemoryRequest(reason="Should fail because it is already active."),
        "bad-approval",
    )
    assert isinstance(result, Failure)
    assert result.failure().kind.value == "conflict"
