import logging
import os
import unittest
from pathlib import Path

TEMP_TEST_DIR = "temp-test-folder"
INTEGRATION_TEST_LEVEL = 1
LARGE_DATA_TEST_LEVEL = 2


def get_test_logger(logger_name):
    logger = logging.getLogger(logger_name)
    Path("unittest-logs").mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(f"unittest-logs/{logger_name}.log")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s \n\n%(message)s\n")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    return logger


def is_test_installed_module():
    return (
        "PMM_TEST_INSTALLED_MODULE" in os.environ
        and os.environ["PMM_TEST_INSTALLED_MODULE"].lower() == "true"
    )


def get_test_level(default=0):
    value = os.getenv("PMM_TEST_LEVEL", default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def skip_unless_test_level(level, reason=None):
    return unittest.skipIf(
        get_test_level() < level,
        reason or f"set PMM_TEST_LEVEL>={level} to run this test",
    )
