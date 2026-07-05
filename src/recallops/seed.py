from __future__ import annotations

from returns.result import Failure

from recallops.config import get_settings
from recallops.runtime import get_service


def run() -> None:
    settings = get_settings()
    result = get_service().seed_demo(settings.demo_project)
    if isinstance(result, Failure):
        error = result.failure()
        raise SystemExit(f"{error.message} [{error.correlation_id}]")
    memory = result.unwrap()
    print(f"Seeded {memory.project}: {memory.statement}")


if __name__ == "__main__":
    run()
