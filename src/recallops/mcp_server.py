from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from returns.result import Failure

from recallops.models import (
    AgentName,
    EvidenceReference,
    HandoffRequest,
    MemoryKind,
    RecallRequest,
    RecordMemoryRequest,
)
from recallops.runtime import get_service

mcp = FastMCP(
    "RecallOps",
    instructions=(
        "Use RecallOps to record high-value project decisions and retrieve reviewed "
        "project truth. Do not record secrets, raw logs, or transient chatter."
    ),
)


def _result_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, Failure):
        error = result.failure()
        return {
            "ok": False,
            "error": {
                "kind": error.kind.value,
                "message": error.message,
                "correlation_id": error.correlation_id,
            },
        }
    value = result.unwrap()
    return {
        "ok": True,
        "data": value.model_dump(mode="json") if hasattr(value, "model_dump") else value,
    }


@mcp.tool()
def recallops_record(
    project: str,
    agent: AgentName,
    session_id: str,
    kind: MemoryKind,
    subject: str,
    statement: str,
    evidence_label: str,
    evidence_uri: str,
    evidence_excerpt: str = "",
    confidence: float = 0.8,
) -> dict[str, Any]:
    """Record a high-value candidate memory for human review."""
    return _result_payload(
        get_service().record(
            RecordMemoryRequest(
                project=project,
                agent=agent,
                session_id=session_id,
                kind=kind,
                subject=subject,
                statement=statement,
                evidence=(
                    EvidenceReference(
                        label=evidence_label,
                        uri=evidence_uri,
                        excerpt=evidence_excerpt,
                    ),
                ),
                confidence=confidence,
            )
        )
    )


@mcp.tool()
def recallops_recall(
    project: str,
    query: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Recall only reviewed, current project truth with provenance."""
    return _result_payload(
        get_service().recall(RecallRequest(project=project, query=query, session_id=session_id))
    )


@mcp.tool()
def recallops_handoff(
    project: str,
    goal: str,
    target_agent: AgentName = AgentName.OPENCODE,
) -> dict[str, Any]:
    """Prepare a deterministic current-truth handoff for a fresh agent."""
    return _result_payload(
        get_service().handoff(HandoffRequest(project=project, goal=goal, target_agent=target_agent))
    )


def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
