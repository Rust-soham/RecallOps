from __future__ import annotations

from typing import Protocol

import httpx
from pydantic import TypeAdapter, ValidationError
from returns.result import Failure, Success

from recallops.config import Settings
from recallops.errors import AppError, AppResult, ErrorKind
from recallops.models import EvidenceReference, GatewayRecall, MemoryRecord


class CogneeGateway(Protocol):
    @property
    def mode(self) -> str: ...

    def remember(self, memory: MemoryRecord, dataset: str, session_id: str) -> AppResult[str]: ...

    def improve(self, dataset: str, session_ids: tuple[str, ...]) -> AppResult[None]: ...

    def recall(self, query: str, dataset: str) -> AppResult[GatewayRecall]: ...


class DemoCogneeGateway:
    """Deterministic adapter used until a Cognee endpoint is configured."""

    @property
    def mode(self) -> str:
        return "demo"

    def remember(self, memory: MemoryRecord, dataset: str, session_id: str) -> AppResult[str]:
        del dataset, session_id
        return Success(str(memory.id))

    def improve(self, dataset: str, session_ids: tuple[str, ...]) -> AppResult[None]:
        del dataset, session_ids
        return Success(None)

    def recall(self, query: str, dataset: str) -> AppResult[GatewayRecall]:
        del query, dataset
        return Success(GatewayRecall(source="demo-graph"))


class HttpCogneeGateway:
    def __init__(self, settings: Settings) -> None:
        headers = {"Accept": "application/json"}
        if settings.cognee_api_key:
            headers["X-Api-Key"] = settings.cognee_api_key
        if settings.cognee_tenant_id:
            headers["X-Tenant-Id"] = settings.cognee_tenant_id
        self._client = httpx.Client(
            base_url=settings.cognee_base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(settings.request_timeout_seconds),
        )

    @property
    def mode(self) -> str:
        return "cognee"

    def remember(self, memory: MemoryRecord, dataset: str, session_id: str) -> AppResult[str]:
        document = "\n".join(
            (
                f"RecallOps memory ID: {memory.id}",
                f"Kind: {memory.kind.value}",
                f"Subject: {memory.subject}",
                f"Statement: {memory.statement}",
                "Evidence:",
                *(
                    f"- {reference.label}: {reference.uri}\n  {reference.excerpt}"
                    for reference in memory.evidence
                ),
            )
        )
        form = {
            "datasetName": dataset,
            "session_id": session_id,
            "run_in_background": "false",
        }
        try:
            response = self._client.post(
                "/api/v1/remember",
                data=form,
                files={
                    "data": (
                        f"recallops-{memory.id}.txt",
                        document.encode(),
                        "text/plain",
                    )
                },
            )
            response.raise_for_status()
            body: object = response.json()
        except httpx.TimeoutException as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_TIMEOUT,
                    "Cognee did not finish remembering the memory in time.",
                    cause=exc,
                )
            )
        except (httpx.HTTPError, ValueError) as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_UNAVAILABLE,
                    "Cognee could not remember the memory.",
                    cause=exc,
                )
            )
        if not isinstance(body, dict):
            return Failure(
                AppError(
                    ErrorKind.COGNEE_MALFORMED_RESPONSE,
                    "Cognee returned an invalid remember response.",
                )
            )
        entry_id = body.get("entry_id") or body.get("id") or str(memory.id)
        return Success(str(entry_id))

    def improve(self, dataset: str, session_ids: tuple[str, ...]) -> AppResult[None]:
        improve_payload: dict[str, object] = {
            "dataset_name": dataset,
            "session_ids": list(session_ids),
            "run_in_background": False,
        }
        try:
            response = self._client.post("/api/v1/improve", json=improve_payload)
            if response.status_code == 404:
                # Cognee Cloud's synchronous /remember endpoint already bridges
                # session memory into the graph. Cloud does not expose /improve,
                # and calling /cognify again can race its automatic bridge.
                return Success(None)
            response.raise_for_status()
            return Success(None)
        except httpx.TimeoutException as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_TIMEOUT,
                    "Cognee did not finish improving the memory in time.",
                    cause=exc,
                )
            )
        except httpx.HTTPError as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_UNAVAILABLE,
                    "Cognee could not improve the project memory.",
                    cause=exc,
                )
            )

    def recall(self, query: str, dataset: str) -> AppResult[GatewayRecall]:
        response_result = self._post(
            "/api/v1/recall",
            {
                "query": query,
                "search_type": None,
                "datasets": [dataset],
                "scope": "graph",
                "only_context": True,
                "include_references": True,
            },
            empty_when_recall_uninitialized=True,
        )
        if isinstance(response_result, Failure):
            return response_result
        raw = response_result.unwrap()
        results = raw if isinstance(raw, list) else [raw]
        entry_ids: list[str] = []
        references: list[EvidenceReference] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            candidate_id = item.get("id") or item.get("entry_id")
            if candidate_id:
                entry_ids.append(str(candidate_id))
            raw_references = item.get("references", [])
            if isinstance(raw_references, list):
                for reference in raw_references:
                    if isinstance(reference, dict):
                        references.append(
                            EvidenceReference(
                                label=str(reference.get("document_name", "Cognee source")),
                                uri=str(
                                    reference.get("document_id")
                                    or reference.get("source")
                                    or "cognee://memory"
                                ),
                                excerpt=str(reference.get("text", ""))[:1000],
                            )
                        )
        try:
            return Success(
                GatewayRecall(
                    entry_ids=tuple(entry_ids),
                    references=TypeAdapter(tuple[EvidenceReference, ...]).validate_python(
                        tuple(references)
                    ),
                    source="cognee-graph",
                )
            )
        except ValidationError as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_MALFORMED_RESPONSE,
                    "Cognee returned malformed reference data.",
                    cause=exc,
                )
            )

    def _post(
        self,
        path: str,
        payload: dict[str, object],
        *,
        empty_when_recall_uninitialized: bool = False,
    ) -> AppResult[dict[str, object] | list[object]]:
        try:
            response = self._client.post(path, json=payload)
            if empty_when_recall_uninitialized and response.status_code == 404:
                error_body: object = response.json()
                if (
                    isinstance(error_body, dict)
                    and error_body.get("error") == "Recall prerequisites not met"
                ):
                    return Success([])
            response.raise_for_status()
            body: object = response.json()
            if not isinstance(body, (dict, list)):
                raise ValueError("Expected a JSON object or list.")
            return Success(body)
        except httpx.TimeoutException as exc:
            return Failure(
                AppError(ErrorKind.COGNEE_TIMEOUT, "Cognee did not respond in time.", cause=exc)
            )
        except (httpx.HTTPError, ValueError) as exc:
            return Failure(
                AppError(
                    ErrorKind.COGNEE_UNAVAILABLE,
                    "Cognee is unavailable or returned an invalid response.",
                    cause=exc,
                )
            )


def build_gateway(settings: Settings) -> CogneeGateway:
    if settings.cognee_mode == "http":
        return HttpCogneeGateway(settings)
    return DemoCogneeGateway()
