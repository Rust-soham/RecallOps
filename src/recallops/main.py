from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from recallops import __version__
from recallops.api import router
from recallops.config import get_settings
from recallops.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="RecallOps API",
        version=__version__,
        description="Trust and governance for shared AI-agent memory.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.include_router(router)
    web_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    if web_dist.is_dir():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    return app


app = create_app()


def run() -> None:
    uvicorn.run("recallops.main:app", host="127.0.0.1", port=8787, reload=False)
