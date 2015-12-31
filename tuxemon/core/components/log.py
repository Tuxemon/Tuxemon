#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# core.components.log Logging module.
#
#

import os
import sys
import logging
from . import config as Config

# read the configuration file
BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".." + os.sep + "..")) + os.sep
if "library.zip" in BASEDIR:
    BASEDIR = os.path.abspath(os.path.join(BASEDIR, "..")) + os.sep

# Set our logging levels
LOG_LEVELS = {"debug": logging.DEBUG,
              "info": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "critical": logging.CRITICAL}
config_path = BASEDIR + "tuxemon.cfg"
config = Config.Config(config_path)
loggers = {}

if config.debug_level in LOG_LEVELS:
    log_level = LOG_LEVELS[config.debug_level]
else:
    log_level = logging.INFO

# Set up logging if the configuration has it enabled
if config.debug_logging == "1":

    for logger_name in config.loggers:

        # Enable logging
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        log_hdlr = logging.StreamHandler(sys.stdout)
        log_hdlr.setLevel(logging.DEBUG)
        log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "
                                                "%(levelname)s - %(message)s"))
        logger.addHandler(log_hdlr)

        loggers[logger_name] = logger



