import pytest

from workforce_service.config import Settings, load_settings


def test_default_settings(monkeypatch):
    monkeypatch.delenv("WORKFORCE_ENV", raising=False)
    monkeypatch.delenv("WORKFORCE_PORT", raising=False)

    settings = load_settings()

    assert settings.environment == "development"
    assert settings.port == 9696


def test_environment_is_loaded_from_environment_variable(monkeypatch):
    monkeypatch.setenv("WORKFORCE_ENV", "production")
    monkeypatch.delenv("WORKFORCE_PORT", raising=False)

    settings = load_settings()

    assert settings.environment == "production"


def test_port_is_loaded_as_integer(monkeypatch):
    monkeypatch.setenv("WORKFORCE_PORT", "8080")

    settings = load_settings()

    assert settings.port == 8080
    assert isinstance(settings.port, int)


@pytest.mark.parametrize(
    "invalid_port",
    ["abc", "0", "65536", "-1"],
)
def test_invalid_port_from_environment_is_rejected(monkeypatch, invalid_port):
    monkeypatch.setenv("WORKFORCE_PORT", invalid_port)

    with pytest.raises((TypeError, ValueError), match="port|WORKFORCE_PORT"):
        load_settings()


def test_empty_environment_is_rejected(monkeypatch):
    monkeypatch.setenv("WORKFORCE_ENV", "   ")

    with pytest.raises(ValueError, match="environment|WORKFORCE_ENV"):
        load_settings()


def test_direct_settings_construction_rejects_invalid_environment():
    with pytest.raises(ValueError, match="environment"):
        Settings(environment="", port=9696)


@pytest.mark.parametrize("invalid_port", [0, 65536, -1])
def test_direct_settings_construction_rejects_invalid_port(invalid_port):
    with pytest.raises(ValueError, match="port"):
        Settings(environment="development", port=invalid_port)


def test_direct_settings_construction_rejects_non_integer_port():
    with pytest.raises(TypeError, match="port"):
        Settings(environment="development", port="9696")


def test_settings_are_immutable():
    settings = Settings()

    with pytest.raises(AttributeError):
        settings.port = 8080