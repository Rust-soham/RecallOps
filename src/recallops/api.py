from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from returns.result import Failure, Result

from recallops.errors import AppError, ErrorKind
from recallops.models import (
    ApproveMemoryRequest,
    ConflictRecord,
    HandoffPack,
    HandoffRequest,
    MemoryRecord,
    ProjectOverview,
    RecallRequest,
    RecallResult,
    RecordMemoryRequest,
)
from recallops.runtime import get_service

router = APIRouter(prefix="/api")


def _unwrap[T](result: Result[T, AppError]) -> T:
    if not isinstance(result, Failure):
        return result.unwrap()
    error = result.failure()
    status_code = {
        ErrorKind.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorKind.CONFLICT: status.HTTP_409_CONFLICT,
        ErrorKind.VALIDATION: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorKind.COGNEE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
        ErrorKind.COGNEE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorKind.COGNEE_MALFORMED_RESPONSE: status.HTTP_502_BAD_GATEWAY,
        ErrorKind.PERSISTENCE: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorKind.INTERNAL: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }[error.kind]
    raise HTTPException(
        status_code=status_code,
        detail={
            "kind": error.kind.value,
            "message": error.message,
            "correlation_id": error.correlation_id,
        },
    )


@router.get("/health")
def health() -> dict[str, str]:
    get_service()
    return {"status": "ok", "service": "recallops"}


@router.get("/projects/{project}/overview")
def overview(project: str) -> ProjectOverview:
    return _unwrap(get_service().overview(project))


@router.get("/projects/{project}/memories")
def memories(project: str) -> tuple[MemoryRecord, ...]:
    return _unwrap(get_service().list_memories(project))


@router.get("/projects/{project}/conflicts")
def conflicts(project: str) -> tuple[ConflictRecord, ...]:
    return _unwrap(get_service().list_conflicts(project))


@router.post("/memories", status_code=status.HTTP_201_CREATED)
def record_memory(request: RecordMemoryRequest) -> MemoryRecord:
    return _unwrap(get_service().record(request))


@router.post("/memories/{memory_id}/approve")
def approve_memory(
    memory_id: UUID,
    request: ApproveMemoryRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> MemoryRecord:
    return _unwrap(get_service().approve(memory_id, request, idempotency_key))


@router.post("/recall")
def recall(request: RecallRequest) -> RecallResult:
    return _unwrap(get_service().recall(request))


@router.post("/handoffs")
def handoff(request: HandoffRequest) -> HandoffPack:
    return _unwrap(get_service().handoff(request))


@router.post("/projects/{project}/reset")
def reset(project: str) -> MemoryRecord:
    return _unwrap(get_service().seed_demo(project))


@router.get("/events/stream")
def event_stream(
    project: str = Query(min_length=2, max_length=100),
) -> StreamingResponse:
    async def generate() -> AsyncIterator[str]:
        last_payload = ""
        while True:
            overview_result = get_service().overview(project)
            if not isinstance(overview_result, Failure):
                payload = overview_result.unwrap().model_dump_json()
                if payload != last_payload:
                    yield f"data: {payload}\n\n"
                    last_payload = payload
            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream")
