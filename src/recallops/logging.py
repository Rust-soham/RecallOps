from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping, MutableMapping
from typing import Any

import structlog

SECRET_PATTERN = re.compile(r"(?i)(bearer\s+|api[_-]?key[=:]\s*)[A-Za-z0-9._-]+")


def redact(value: str) -> str:
    return SECRET_PATTERN.sub(r"\1<redacted>", value)


def _redact_event(
    _logger: object, _method_name: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    for key, value in tuple(event_dict.items()):
        if isinstance(value, str):
            event_dict[key] = redact(value)
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stderr, level=logging.INFO)
    renderer: structlog.types.Processor = (
        structlog.dev.ConsoleRenderer()
        if sys.stderr.isatty()
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_event,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
