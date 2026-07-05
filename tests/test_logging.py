from recallops.logging import redact


def test_secret_redaction() -> None:
    assert redact("Authorization: Bearer abc.DEF-123") == "Authorization: Bearer <redacted>"
    assert redact("api_key=secret-value") == "api_key=<redacted>"
