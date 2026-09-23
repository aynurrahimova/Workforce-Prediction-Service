from __future__ import annotations

import pytest

from workforce_service.config import Settings, load_settings


# P2-S3 regression tests
def test_default_settings():
    assert load_settings() == Settings()


def test_default_environment():
    assert load_settings().environment == "development"


def test_default_port():
    assert load_settings().port == 9696


def test_environment_is_loaded_from_environment_variable(monkeypatch):
    monkeypatch.setenv("WORKFORCE_ENV", "production")
    assert load_settings().environment == "production"


def test_environment_is_stripped(monkeypatch):
    monkeypatch.setenv("WORKFORCE_ENV", " production ")
    assert load_settings().environment == "production"


def test_port_is_loaded_from_environment_variable(monkeypatch):
    monkeypatch.setenv("WORKFORCE_PORT", "8080")
    assert load_settings().port == 8080


def test_settings_accepts_custom_environment_and_port():
    settings = Settings(environment="staging", port=8080)

    assert settings.environment == "staging"
    assert settings.port == 8080


def test_settings_is_immutable():
    settings = Settings()

    with pytest.raises(AttributeError):
        settings.port = 8080


def test_invalid_environment_type_is_rejected():
    with pytest.raises(TypeError, match="environment"):
        Settings(environment=123)


def test_empty_environment_is_rejected():
    with pytest.raises(ValueError, match="environment"):
        Settings(environment="   ")


def test_invalid_port_type_is_rejected():
    with pytest.raises(TypeError, match="port"):
        Settings(port="9696")


def test_boolean_port_is_rejected():
    with pytest.raises(TypeError, match="port"):
        Settings(port=True)


def test_port_range_is_enforced():
    with pytest.raises(
        ValueError,
        match="between 1 and 65535",
    ):
        Settings(port=0)


def test_non_integer_port_environment_value_is_rejected(monkeypatch):
    monkeypatch.setenv("WORKFORCE_PORT", "not-a-port")

    with pytest.raises(ValueError, match="WORKFORCE_PORT"):
        load_settings()


# P2-S4 additions
def test_default_logging_level(monkeypatch):
    monkeypatch.delenv(
        "WORKFORCE_LOG_LEVEL",
        raising=False,
    )

    settings = load_settings()

    assert settings.logging_level == "INFO"


def test_logging_level_is_loaded_from_environment_variable(monkeypatch):
    monkeypatch.setenv(
        "WORKFORCE_LOG_LEVEL",
        "DEBUG",
    )

    settings = load_settings()

    assert settings.logging_level == "DEBUG"


def test_logging_level_is_normalized(monkeypatch):
    monkeypatch.setenv(
        "WORKFORCE_LOG_LEVEL",
        "debug",
    )

    settings = load_settings()

    assert settings.logging_level == "DEBUG"


@pytest.mark.parametrize(
    "logging_level",
    [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ],
)
def test_supported_logging_levels_are_accepted(logging_level):
    settings = Settings(
        logging_level=logging_level,
    )

    assert settings.logging_level == logging_level


def test_invalid_logging_level_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "WORKFORCE_LOG_LEVEL",
        "VERBOSE",
    )

    with pytest.raises(
        ValueError,
        match="logging_level",
    ):
        load_settings()


def test_direct_settings_construction_rejects_invalid_logging_level():
    with pytest.raises(
        ValueError,
        match="logging_level",
    ):
        Settings(logging_level="VERBOSE")
