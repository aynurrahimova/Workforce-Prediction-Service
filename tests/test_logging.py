from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pytest

from workforce_service.config import Settings
from workforce_service.observability import configure_logging, get_logger


_LOGGER_NAME = "workforce_service"
_HANDLER_MARKER = "_workforce_service_foundation_handler"


def _foundation_handlers() -> list[logging.Handler]:
    logger = logging.getLogger(_LOGGER_NAME)
    return [
        handler
        for handler in logger.handlers
        if getattr(handler, _HANDLER_MARKER, False)
    ]


def _reset_logging() -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    for handler in _foundation_handlers():
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True


@pytest.fixture(autouse=True)
def clean_logging():
    _reset_logging()
    yield
    _reset_logging()


def test_get_logger_returns_standard_logger():
    logger = get_logger("workforce_service.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "workforce_service.test"


def test_package_logger_is_configured_at_requested_level():
    configure_logging(Settings(logging_level="WARNING"))
    logger = logging.getLogger(_LOGGER_NAME)
    assert logger.level == logging.WARNING
    assert logger.propagate is False


def test_configured_level_controls_emission(capsys):
    configure_logging(Settings(logging_level="INFO"))
    logger = get_logger("workforce_service.test")

    logger.debug("debug message")
    logger.info("info message")

    captured = capsys.readouterr()
    assert "debug message" not in captured.err
    assert "info message" in captured.err


def test_child_loggers_use_normal_propagation():
    configure_logging(Settings())
    child = get_logger("workforce_service.child")
    assert child.propagate is True


def test_root_logger_is_unchanged():
    root = logging.getLogger()
    original_level = root.level
    original_handlers = list(root.handlers)
    original_propagate = root.propagate

    configure_logging(Settings())

    assert root.level == original_level
    assert list(root.handlers) == original_handlers
    assert root.propagate == original_propagate
    assert not _foundation_handlers_in_root(root)


def _foundation_handlers_in_root(root: logging.Logger) -> list[logging.Handler]:
    return [
        handler
        for handler in root.handlers
        if getattr(handler, _HANDLER_MARKER, False)
    ]


def test_structured_output_is_valid_json(capsys):
    configure_logging(Settings())
    get_logger("workforce_service.test").info("test message")

    record = json.loads(capsys.readouterr().err.strip())
    assert isinstance(record, dict)


def test_structured_output_contains_required_fields(capsys):
    configure_logging(Settings())
    get_logger("workforce_service.test").info("test message")

    record = json.loads(capsys.readouterr().err.strip())
    assert set(
        ("timestamp", "level", "logger", "message", "environment")
    ) <= record.keys()
    assert record["level"] == "INFO"
    assert record["logger"] == "workforce_service.test"
    assert record["message"] == "test message"
    assert record["environment"] == "development"


def test_timestamp_is_utc_and_derived_from_record_created(capsys):
    configure_logging(Settings())
    logger = get_logger("workforce_service.test")

    captured_records: list[logging.LogRecord] = []

    class RecordCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_records.append(record)

    capture_handler = RecordCapture()
    package_logger = logging.getLogger(_LOGGER_NAME)
    package_logger.addHandler(capture_handler)
    try:
        logger.info("timestamp test")
    finally:
        package_logger.removeHandler(capture_handler)
        capture_handler.close()

    record = json.loads(capsys.readouterr().err.strip())
    parsed = datetime.fromisoformat(record["timestamp"])
    expected = datetime.fromtimestamp(
        captured_records[0].created,
        tz=timezone.utc,
    )

    assert parsed.tzinfo == timezone.utc
    assert parsed == expected


def test_public_observability_api_excludes_formatter():
    import workforce_service.observability as observability

    assert observability.__all__ == ["configure_logging", "get_logger"]
    assert not hasattr(observability, "JsonFormatter")


def test_environment_comes_from_settings(capsys):
    configure_logging(Settings(environment="production"))
    get_logger("workforce_service.test").info("environment test")

    record = json.loads(capsys.readouterr().err.strip())
    assert record["environment"] == "production"


def test_exception_information_is_structured(capsys):
    configure_logging(Settings())
    logger = get_logger("workforce_service.test")

    try:
        raise ValueError("test failure")
    except ValueError:
        logger.exception("operation failed")

    record = json.loads(capsys.readouterr().err.strip())
    assert record["message"] == "operation failed"
    assert "exception" in record
    assert "ValueError" in record["exception"]
    assert "test failure" in record["exception"]


def test_foundation_handler_is_owned_and_unrelated_handler_is_preserved():
    logger = logging.getLogger(_LOGGER_NAME)
    unrelated = logging.NullHandler()
    logger.addHandler(unrelated)

    try:
        configure_logging(Settings())

        assert unrelated in logger.handlers
        assert len(_foundation_handlers()) == 1
        assert _foundation_handlers()[0] is not unrelated
    finally:
        logger.removeHandler(unrelated)
        unrelated.close()


def test_repeated_configuration_reuses_same_handler():
    settings = Settings()
    configure_logging(settings)
    first = _foundation_handlers()[0]

    configure_logging(settings)
    second = _foundation_handlers()[0]

    assert first is second
    assert len(_foundation_handlers()) == 1


def test_reconfiguration_updates_level_and_environment_without_replacing_handler():
    configure_logging(
        Settings(logging_level="INFO", environment="development")
    )
    handler = _foundation_handlers()[0]

    configure_logging(
        Settings(logging_level="DEBUG", environment="production")
    )
    reconfigured = _foundation_handlers()[0]
    package_logger = logging.getLogger(_LOGGER_NAME)

    assert reconfigured is handler
    assert len(_foundation_handlers()) == 1
    assert package_logger.level == logging.DEBUG
    assert handler.level == logging.DEBUG

    formatter = handler.formatter
    assert formatter is not None
    assert getattr(formatter, "_environment") == "production"