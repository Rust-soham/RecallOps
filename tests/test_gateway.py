from pathlib import Path

import httpx
import respx
from returns.result import Failure, Success

from recallops.config import Settings
from recallops.gateway import HttpCogneeGateway
from recallops.models import (
    AgentName,
    EvidenceReference,
    MemoryKind,
    MemoryRecord,
    MemoryStatus,
)


def memory() -> MemoryRecord:
    return MemoryRecord(
        project="demo",
        agent=AgentName.CODEX,
        session_id="codex:1",
        kind=MemoryKind.DECISION,
        subject="auth.session",
        statement="Use secure cookie sessions.",
        evidence=(EvidenceReference(label="review", uri="docs/review.md"),),
        confidence=0.9,
        status=MemoryStatus.CANDIDATE,
    )


def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "db.sqlite",
        cognee_mode="http",
        cognee_base_url="https://cognee.test",
        cognee_api_key="secret",
        cognee_tenant_id="tenant-123",
    )


@respx.mock
def test_http_gateway_remember_and_recall_references(tmp_path: Path) -> None:
    respx.post("https://cognee.test/api/v1/remember").mock(
        return_value=httpx.Response(200, json={"entry_id": "entry-1"})
    )
    respx.post("https://cognee.test/api/v1/recall").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "entry-1",
                    "references": [
                        {
                            "document_name": "Security review",
                            "document_id": "docs/review.md",
                            "text": "Use an HTTP-only cookie.",
                        }
                    ],
                }
            ],
        )
    )
    gateway = HttpCogneeGateway(settings(tmp_path))
    remembered = gateway.remember(memory(), "recallops:demo:working", "codex:1")
    recalled = gateway.recall("How does auth work?", "recallops:demo:current")
    assert isinstance(remembered, Success)
    assert remembered.unwrap() == "entry-1"
    assert isinstance(recalled, Success)
    assert recalled.unwrap().references[0].uri == "docs/review.md"
    remember_request = respx.calls[0].request
    assert remember_request.headers["X-Api-Key"] == "secret"
    assert remember_request.headers["X-Tenant-Id"] == "tenant-123"
    assert "multipart/form-data" in remember_request.headers["Content-Type"]


@respx.mock
def test_http_gateway_accepts_cloud_automatic_improvement(tmp_path: Path) -> None:
    respx.post("https://cognee.test/api/v1/improve").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )
    result = HttpCogneeGateway(settings(tmp_path)).improve(
        "recallops:demo:current", ("approved:1",)
    )
    assert isinstance(result, Success)


@respx.mock
def test_http_gateway_treats_uninitialized_dataset_as_empty_recall(
    tmp_path: Path,
) -> None:
    respx.post("https://cognee.test/api/v1/recall").mock(
        return_value=httpx.Response(
            404,
            json={
                "error": "Recall prerequisites not met",
                "hint": "Remember something before recalling.",
            },
        )
    )
    result = HttpCogneeGateway(settings(tmp_path)).recall(
        "How does auth work?", "recallops:demo:current"
    )
    assert isinstance(result, Success)
    assert result.unwrap().entry_ids == ()
    assert result.unwrap().references == ()


@respx.mock
def test_http_gateway_timeout_is_typed(tmp_path: Path) -> None:
    respx.post("https://cognee.test/api/v1/recall").mock(side_effect=httpx.ReadTimeout("slow"))
    result = HttpCogneeGateway(settings(tmp_path)).recall(
        "How does auth work?", "recallops:demo:current"
    )
    assert isinstance(result, Failure)
    assert result.failure().kind.value == "cognee_timeout"
