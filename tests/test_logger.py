import datadog_serverless_compat
import logging
import pytest


def test_logger_has_custom_log_levels():
    try:
        # Added in version 3.11
        level_mapping = logging.getLevelNamesMapping()
    except AttributeError:
        level_mapping = {name: num for num, name in logging._levelToName.items()}

    assert level_mapping == {
        "CRITICAL": 50,
        "FATAL": 50,
        "ERROR": 40,
        "WARN": 30,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
        "NOTSET": 0,
        "TRACE": 5,
        "OFF": 100,
    }


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("INFO", "INFO"),
        ("info", "INFO"),
        ("", "INFO"),
        ("INVALID", "INFO"),
        ("TRACE", "TRACE"),
    ],
)
def test_logger_level_initialization_from_env_var(monkeypatch, test_input, expected):
    monkeypatch.setenv("DD_LOG_LEVEL", test_input)

    logger = logging.getLogger(__name__)

    datadog_serverless_compat.initialize_logging(__name__)

    level = logger.getEffectiveLevel()
    level_name = logging.getLevelName(level)

    assert level_name == expected


def test_logger_level_initialization_from_env_var_none(monkeypatch):
    monkeypatch.delenv("DD_LOG_LEVEL", raising=False)

    logger = logging.getLogger(__name__)

    datadog_serverless_compat.initialize_logging(__name__)

    level = logger.getEffectiveLevel()
    level_name = logging.getLevelName(level)

    assert level_name == "INFO"
