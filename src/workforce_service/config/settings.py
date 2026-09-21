from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ENV = "development"
DEFAULT_PORT = 9696


def _validate_environment(environment: str) -> str:
    """Validate and normalize the service environment."""
    if not isinstance(environment, str):
        raise TypeError("environment must be a string.")

    environment = environment.strip()

    if not environment:
        raise ValueError("environment must not be empty.")

    return environment


def _validate_port(port: int) -> int:
    """Validate a TCP port number."""
    if isinstance(port, bool) or not isinstance(port, int):
        raise TypeError("port must be an integer.")

    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535.")

    return port


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration for the workforce prediction service."""

    environment: str = DEFAULT_ENV
    port: int = DEFAULT_PORT

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "environment",
            _validate_environment(self.environment),
        )
        object.__setattr__(self, "port", _validate_port(self.port))


def _parse_environment(value: str | None) -> str:
    """Read the service environment from the process environment."""
    return _validate_environment(
        value if value is not None else DEFAULT_ENV
    )


def _parse_port(value: str | None) -> int:
    """Read and validate the service port from the process environment."""
    if value is None:
        return DEFAULT_PORT

    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("WORKFORCE_PORT must be an integer.") from exc

    return _validate_port(port)


def load_settings() -> Settings:
    """Load service settings from environment variables."""
    return Settings(
        environment=_parse_environment(os.getenv("WORKFORCE_ENV")),
        port=_parse_port(os.getenv("WORKFORCE_PORT")),
    )