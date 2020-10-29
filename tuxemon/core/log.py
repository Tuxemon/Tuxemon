#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# core.log Logging module.
#
#


import logging
import sys

from tuxemon.core import prepare


def configure():
    """Configure logging based on the settings in the config file.
    """
    # Set our logging levels
    LOG_LEVELS = {"debug": logging.DEBUG,
                  "info": logging.INFO,
                  "warning": logging.WARNING,
                  "error": logging.ERROR,
                  "critical": logging.CRITICAL}
    config = prepare.CONFIG
    loggers = {}

    if config.debug_level in LOG_LEVELS:
        log_level = LOG_LEVELS[config.debug_level]
    else:
        log_level = logging.INFO

    # Set up logging if the configuration has it enabled
    if config.debug_logging:

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
            log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "
                                                    "%(levelname)s - %(message)s"))
            logger.addHandler(log_hdlr)

            loggers[logger_name] = logger
