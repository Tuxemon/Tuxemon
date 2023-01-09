# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import sys
import warnings

from tuxemon import prepare


def configure():
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

            # Enable logging for all modules if specified.
            if logger_name == "all":
                print("Enabling logging of all modules.")
                logger = logging.getLogger()
            else:
                print("Enabling logging for module: %s" % logger_name)
                logger = logging.getLogger(logger_name)

            # Enable logging
            logger.setLevel(log_level)
            log_hdlr = logging.StreamHandler(sys.stdout)
            log_hdlr.setLevel(log_level)
            log_hdlr.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - " "%(levelname)s - %(message)s"
                )
            )
            logger.addHandler(log_hdlr)

            loggers[logger_name] = logger

            # prevent pyscroll redraw warnings
            pyscroll_logger = logging.getLogger("orthographic")
            pyscroll_logger.setLevel(logging.ERROR)
