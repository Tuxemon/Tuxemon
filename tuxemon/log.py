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


def get_git_hash() -> str:
    """Gets the current Git hash."""
    try:
        return (
            subprocess.check_output(["git", "describe", "--always"])
            .strip()
            .decode()
        )
    except subprocess.CalledProcessError:
        logging.warning("Git command failed. Git hash not available.")
        return "N/A"
    except FileNotFoundError:
        logging.warning("Git not found. Git hash not available.")
        return "N/A"


def configure() -> None:
    """Configures logging based on the settings in the config file."""
    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    config = prepare.CONFIG.logging
    loggers = {}

    log_level = LOG_LEVELS.get(config.debug_level, logging.INFO)

    if config.debug_logging:
        warnings.filterwarnings("default")

        githash = get_git_hash()
        print(f"Git Hash: {githash}")

        for logger_name in config.loggers:
            if logger_name == "all":
                print("Enabling logging of all modules.")
                logger = logging.getLogger()
            else:
                print(f"Enabling logging for module: {logger_name}")
                logger = logging.getLogger(logger_name)

            log_formatter = logging.Formatter(
                "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
            )
            logger.setLevel(log_level)
            log_strm = logging.StreamHandler(sys.stdout)
            log_strm.setLevel(log_level)
            log_strm.setFormatter(log_formatter)
            logger.addHandler(log_strm)

            if config.log_to_file:
                log_dir = os.path.realpath(f"{paths.USER_STORAGE_DIR}/logs")
                os.makedirs(
                    log_dir, exist_ok=True
                )  # creates the directory if it does not exists.
                if config.log_keep_max > 0:
                    log_dir_files = {
                        entry.name: entry.stat().st_mtime
                        for entry in os.scandir(log_dir)
                        if entry.is_file()
                    }
                    sorted_files = sorted(
                        log_dir_files.items(), key=itemgetter(1), reverse=True
                    )

                    if len(sorted_files) > config.log_keep_max:
                        for x in range(config.log_keep_max, len(sorted_files)):
                            filename = sorted_files[x][0]
                            file_path = os.path.join(log_dir, filename)
                            os.remove(file_path)

                    formatted_time = time.strftime(
                        "%Y-%m-%d_%Hh%Mm%Ss", time.localtime()
                    )
                    log_file = logging.FileHandler(
                        os.path.join(log_dir, f"{formatted_time}.log")
                    )
                    log_file.setFormatter(log_formatter)
                    log_file.setLevel(log_level)
                    logger.addHandler(log_file)

            loggers[logger_name] = logger

        pyscroll_logger = logging.getLogger("orthographic")
        pyscroll_logger.setLevel(logging.ERROR)
