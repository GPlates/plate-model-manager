#
#    Copyright (C) 2024-2026 The University of Sydney, Australia
#
#    This program is free software; you can redistribute it and/or modify it under
#    the terms of the GNU General Public License, version 2, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import logging
import sys
import warnings
from pathlib import Path

from . import settings

pmm_logger = logging.getLogger("pmm")
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d,%H:%M:%S",
)


def setup_logging():
    pmm_logger.propagate = False
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    pmm_logger.addHandler(stdout_handler)
    pmm_logger.setLevel(logging.INFO)

    if is_debug_mode():
        turn_on_debug_logging()

    if settings.enable_log_to_file:
        add_logging_file(settings.log_file)


def add_logging_file(filename: str = "pmm.log", level=logging.INFO):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(filename)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    pmm_logger.addHandler(fh)


def turn_on_debug_logging():
    set_logging_level(logging.DEBUG)
    pmm_logger.debug(f"The debug logging has been enabled.")


def set_logging_level(level=logging.WARNING):
    logger = logging.getLogger("pmm")
    logger.setLevel(level)
    for h in logger.handlers:
        h.setLevel(level)


def disable_stdout_logging():
    pmm_logger.removeHandler(stdout_handler)
    print("The logging to stdout has been disabled.")


def my_warningformat(message, category, filename, lineno, line=None):
    return f"{filename}:{lineno}: {category.__name__}: {message}\n"


warnings.formatwarning = my_warningformat


def print_warning(msg):
    # warnings.warn(msg)
    pmm_logger.warning(msg)


def print_error(msg):
    pmm_logger.error(msg)


def is_debug_mode():
    """Check if the debug mode is enabled via settings.debug.

    export PMM_DEBUG=true, or set debug = true in a settings.toml file, to enable the debug mode.
    """
    return settings.debug


from importlib.metadata import PackageNotFoundError, version


def get_distribution_version():
    """get the version string from the package metadata"""

    try:
        return version("plate_model_manager")
    except PackageNotFoundError:
        return "UNKNOWN VERSION"
