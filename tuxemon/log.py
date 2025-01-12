# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import os
import subprocess
import sys
import time
import warnings
from operator import itemgetter

from tuxemon import prepare
from tuxemon.constants import paths


def configure() -> None:
    """Configure logging based on the settings in the config file."""
    # Set our logging levels
    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    config = prepare.CONFIG
    loggers = {}

    if config.debug_level in LOG_LEVELS:
        log_level = LOG_LEVELS[config.debug_level]
    else:
        log_level = logging.INFO

    # Set up logging if the configuration has it enabled
    if config.debug_logging:
        # Enable suppressed warnings
        warnings.filterwarnings("default")

        for logger_name in config.loggers:
            # Get the current git hash
            try:
                githash = (
                    subprocess.check_output(["git", "describe", "--always"])
                    .strip()
                    .decode()
                )
                print(f"Git Hash: {githash}")
            except:
                print("No Git Hash")

            # Enable logging for all modules if specified.
            if logger_name == "all":
                print("Enabling logging of all modules.")
                logger = logging.getLogger()
            else:
                print("Enabling logging for module: %s" % logger_name)
                logger = logging.getLogger(logger_name)

            # Enable logging
            log_formatter = logging.Formatter(
                "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
            )
            logger.setLevel(log_level)
            log_strm = logging.StreamHandler(sys.stdout)
            log_strm.setLevel(log_level)
            log_strm.setFormatter(log_formatter)
            logger.addHandler(log_strm)

            # Enable logging to file
            if config.log_to_file:
                log_dir = os.path.realpath(f"{paths.USER_STORAGE_DIR}/logs")
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                if config.log_keep_max > 0:
                    log_dir_files = {}
                    for entry in os.listdir(log_dir):
                        log_dir_files[entry] = os.stat(
                            f"{log_dir}/{entry}"
                        ).st_mtime
                    sorted_files = sorted(
                        log_dir_files.items(), key=itemgetter(1), reverse=True
                    )
                    log_dir_files.clear()
                    if len(sorted_files) > config.log_keep_max:
                        for x in range(
                            config.log_keep_max - 1, len(sorted_files)
                        ):
                            os.remove(f"{log_dir}/{sorted_files[x][0]}")
                formatted_time = time.strftime(
                    "%Y-%m-%d_%Hh%Mm%Ss", time.localtime()
                )
                log_file = logging.FileHandler(
                    f"{log_dir}/{formatted_time}.log"
                )
                log_file.setFormatter(log_formatter)
                log_file.setLevel(log_level)
                logger.addHandler(log_file)

            loggers[logger_name] = logger

            # prevent pyscroll redraw warnings
            pyscroll_logger = logging.getLogger("orthographic")
            pyscroll_logger.setLevel(logging.ERROR)
