import logging
from unittest.mock import patch
from src.utils.logger import logger, _level_from_string, ColoredFormatter, COLORS, RESET


def test_level_from_string() -> None:
    assert _level_from_string("DEBUG") == logging.DEBUG
    assert _level_from_string("INFO") == logging.INFO
    assert _level_from_string("WARNING") == logging.WARNING
    assert _level_from_string("ERROR") == logging.ERROR
    assert _level_from_string("CRITICAL") == logging.CRITICAL
    assert _level_from_string("invalid") == logging.INFO  # default
    assert _level_from_string("") == logging.INFO  # default


def test_colored_formatter() -> None:
    formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s")

    # Create a mock record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    assert "Test message" in formatted
    # Should contain color codes
    assert "\033[" in formatted
    assert RESET in formatted


def test_logger_creation() -> None:
    with (
        patch("src.utils.logger._level_from_string") as mock_level,
        patch("src.config.settings") as mock_settings,
    ):
        mock_level.return_value = logging.DEBUG
        mock_settings.logging_level = "DEBUG"

        test_logger = logger("test-logger")
        assert test_logger.name == "test-logger"
        assert test_logger.level == logging.DEBUG
        assert len(test_logger.handlers) == 1

        handler = test_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, ColoredFormatter)


def test_logger_default_name() -> None:
    with patch("src.config.settings") as mock_settings:
        mock_settings.logging_level = "INFO"

        default_logger = logger()
        assert default_logger.name == "astro-server"


def test_colors_dict() -> None:
    assert "DEBUG" in COLORS
    assert "INFO" in COLORS
    assert "ERROR" in COLORS
    assert isinstance(COLORS["INFO"], str)
    assert COLORS["INFO"].startswith("\033[")
