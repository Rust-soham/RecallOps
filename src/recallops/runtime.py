from __future__ import annotations

from functools import lru_cache

from returns.result import Failure

from recallops.config import get_settings
from recallops.gateway import build_gateway
from recallops.service import RecallOpsService
from recallops.store import SQLiteStore


@lru_cache
def get_service() -> RecallOpsService:
    settings = get_settings()
    store = SQLiteStore(settings.database_path)
    initialized = store.initialize()
    if isinstance(initialized, Failure):
        error = initialized.failure()
        raise RuntimeError(f"{error.message} [{error.correlation_id}]") from error.cause
    return RecallOpsService(store, build_gateway(settings))
