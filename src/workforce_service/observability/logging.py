from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from workforce_service.config import Settings


_LOGGER_NAME = "workforce_service"
_HANDLER_MARKER = "_workforce_service_foundation_handler"


class _JsonFormatter(logging.Formatter):
    """Format workforce service log records as structured JSON."""

    def __init__(self, environment: str) -> None:
        super().__init__()
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": self._environment,
        }

        if record.exc_info is not None:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(payload)


def get_logger(name: str) -> logging.Logger:
    """Return a logger within the workforce service hierarchy."""
    return logging.getLogger(name)


def _get_foundation_handlers(
    logger: logging.Logger,
) -> list[logging.Handler]:
    return [
        handler
        for handler in logger.handlers
        if getattr(handler, _HANDLER_MARKER, False)
    ]


def configure_logging(settings: Settings) -> None:
    """Configure structured logging for the workforce service package."""
    logger = logging.getLogger(_LOGGER_NAME)

    logger.setLevel(settings.logging_level)
    logger.propagate = False

    foundation_handlers = _get_foundation_handlers(logger)

    if foundation_handlers:
        handler = foundation_handlers[0]

        for duplicate in foundation_handlers[1:]:
            logger.removeHandler(duplicate)
            duplicate.close()
    else:
        handler = logging.StreamHandler(sys.stderr)
        setattr(handler, _HANDLER_MARKER, True)
        logger.addHandler(handler)

    handler.setLevel(settings.logging_level)
    handler.setFormatter(
        _JsonFormatter(settings.environment)
    )