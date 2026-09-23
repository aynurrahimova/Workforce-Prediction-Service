from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ENV = "development"
DEFAULT_PORT = 9696
DEFAULT_LOG_LEVEL = "INFO"

VALID_LOG_LEVELS = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
)


def _validate_environment(environment: str) -> str:
    if not isinstance(environment, str):
        raise TypeError("environment must be a string.")

    environment = environment.strip()

    if not environment:
        raise ValueError("environment must not be empty.")

    return environment


def _validate_port(port: int) -> int:
    if isinstance(port, bool) or not isinstance(port, int):
        raise TypeError("port must be an integer.")

    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535.")

    return port


def _validate_log_level(logging_level: str) -> str:
    if not isinstance(logging_level, str):
        raise TypeError("logging_level must be a string.")

    logging_level = logging_level.strip().upper()

    if logging_level not in VALID_LOG_LEVELS:
        raise ValueError(
            "logging_level must be one of: "
            + ", ".join(sorted(VALID_LOG_LEVELS))
        )

    return logging_level


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration for the workforce prediction service."""

    environment: str = DEFAULT_ENV
    port: int = DEFAULT_PORT
    logging_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "environment",
            _validate_environment(self.environment),
        )
        object.__setattr__(
            self,
            "port",
            _validate_port(self.port),
        )
        object.__setattr__(
            self,
            "logging_level",
            _validate_log_level(self.logging_level),
        )


def _parse_environment(value: str | None) -> str:
    return _validate_environment(
        value if value is not None else DEFAULT_ENV
    )


def _parse_port(value: str | None) -> int:
    if value is None:
        return DEFAULT_PORT

    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError(
            "WORKFORCE_PORT must be an integer."
        ) from exc

    return _validate_port(port)


def _parse_log_level(value: str | None) -> str:
    return _validate_log_level(
        value if value is not None else DEFAULT_LOG_LEVEL
    )


def load_settings() -> Settings:
    """Load service settings from environment variables."""
    return Settings(
        environment=_parse_environment(os.getenv("WORKFORCE_ENV")),
        port=_parse_port(os.getenv("WORKFORCE_PORT")),
        logging_level=_parse_log_level(
            os.getenv("WORKFORCE_LOG_LEVEL")
        ),
    )
