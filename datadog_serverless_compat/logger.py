import logging
import os

try:
    # Added in version 3.11
    level_mapping = logging.getLevelNamesMapping()
except AttributeError:
    level_mapping = {name: num for num, name in logging._levelToName.items()}

# https://docs.datadoghq.com/agent/troubleshooting/debug_mode/?tab=agentv6v7#agent-log-level
level_mapping.update(
    {
        "TRACE": 5,
        "WARN": logging.WARNING,
        "OFF": 100,
    }
)


def initialize_logging(name):
    logger = logging.getLogger(name)
    str_level = (os.environ.get("DD_LOG_LEVEL") or "INFO").upper()
    level = level_mapping.get(str_level)

    if level is None:
        logger.setLevel(logging.INFO)
        logger.warning("Invalid log level: %s Defaulting to INFO", str_level)
    else:
        logger.setLevel(level)
