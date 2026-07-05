import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from recallops.models import (
    AgentName,
    EvidenceReference,
    MemoryKind,
    RecordMemoryRequest,
)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RecordMemoryRequest.model_validate(
            {
                "project": "demo",
                "agent": "codex",
                "session_id": "codex:1",
                "kind": "decision",
                "subject": "auth.session",
                "statement": "Use cookie sessions.",
                "evidence": [{"label": "review", "uri": "docs/review.md"}],
                "confidence": 0.9,
                "unexpected": True,
            },
            strict=True,
        )


@given(confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
def test_valid_confidence_round_trips(confidence: float) -> None:
    request = RecordMemoryRequest(
        project="demo",
        agent=AgentName.CODEX,
        session_id="codex:1",
        kind=MemoryKind.DECISION,
        subject="auth.session",
        statement="Use secure cookie sessions.",
        evidence=(EvidenceReference(label="review", uri="docs/review.md"),),
        confidence=confidence,
    )
    assert request.confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_invalid_confidence_is_rejected(confidence: float) -> None:
    with pytest.raises(ValidationError):
        RecordMemoryRequest(
            project="demo",
            agent=AgentName.CODEX,
            session_id="codex:1",
            kind=MemoryKind.DECISION,
            subject="auth.session",
            statement="Use secure cookie sessions.",
            evidence=(EvidenceReference(label="review", uri="docs/review.md"),),
            confidence=confidence,
        )
