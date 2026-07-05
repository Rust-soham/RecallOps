from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar
from uuid import uuid4

from returns.result import Result


class ErrorKind(StrEnum):
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    COGNEE_UNAVAILABLE = "cognee_unavailable"
    COGNEE_TIMEOUT = "cognee_timeout"
    COGNEE_MALFORMED_RESPONSE = "cognee_malformed_response"
    PERSISTENCE = "persistence"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class AppError:
    kind: ErrorKind
    message: str
    context: dict[str, str] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    cause: Exception | None = field(default=None, repr=False, compare=False)


T = TypeVar("T")
type AppResult[T] = Result[T, AppError]
