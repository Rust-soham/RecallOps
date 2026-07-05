from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from recallops.config import get_settings
from recallops.main import create_app
from recallops.runtime import get_service


def test_health_and_reset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RECALLOPS_DATABASE_PATH", str(tmp_path / "api.db"))
    get_service.cache_clear()
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        assert test_client.get("/api/health").status_code == 200
        response = test_client.post("/api/projects/auth-migration/reset")
        assert response.status_code == 200
        assert response.json()["status"] == "active"
    get_service.cache_clear()
    get_settings.cache_clear()
