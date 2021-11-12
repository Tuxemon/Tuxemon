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
# log Logging module.
#
#


import logging
import sys

from tuxemon import prepare
from tuxemon.constants.paths import *
import requests
import gzip
from shutil import copyfileobj, move
from os import remove
from os.path import exists
from datetime import datetime
# For messagebox
import tkinter as tk
from tkinter import messagebox

# For gathering system information
import platform

def archive_log():
    """
    Archives specified file, compressing it and renaming it to 
    the current date using the %d-%m-%Y_%H:%M:%S format.
    """
    if not exists(USER_LOG_DIR + "/latest.log"):
        return
    # Compress the file...
    with open(f"{USER_LOG_DIR}/latest.log", "rb") as uncompressed:
        with gzip.open(f"{USER_LOG_DIR}/latest.log.gz", "wb") as compressed:
            copyfileobj(uncompressed, compressed)
    move(f"{USER_LOG_DIR}/latest.log.gz", 
                f"{USER_LOG_DIR}/{datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}.log.gz")
    os.remove(f"{USER_LOG_DIR}/latest.log")
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
            log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - " "%(levelname)s - %(message)s"))
            logger.addHandler(log_hdlr)

            # Archive previous log
            archive_log()
            # Logging to file
            log_filehandler = logging.FileHandler(f"{USER_LOG_DIR}/latest.log")
            log_filehandler.setLevel(logging.INFO)
            log_filehandler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - " "%(levelname)s - %(message)s"))
            logger.addHandler(log_filehandler)

            loggers[logger_name] = logger

            # prevent pyscroll redraw warnings
            pyscroll_logger = logging.getLogger("orthographic")
            pyscroll_logger.setLevel(logging.ERROR)

def send_logs():
    config = prepare.CONFIG
    logging.info("="* 26)

    logging.info("=== System information ===")

    # OS Info
    entries = {
        platform.platform: "platform",
        platform.processor: "processor",
        platform.python_version: "python_version",
        platform.python_implementation: "python_implementation",
    }
    for i in entries:
        logging.info(f"{entries[i]}\t{i()}")

    logging.info("=== Library versions ===")

    lib_entries = {
        "babel": "babel",
        "cbor": "cbor",
        "neteria": "neteria",
        "pillow": "PIL",
        "pygame": "pygame",
        "pyscroll": "pyscroll",
        "pytmx": "pytmx",
        "requests": "requests",
        "natsort": "natsort",
        "PyYaml": "yaml"
    }
    for i in lib_entries:
        try:
            logging.info(f"{i}\t{__import__(lib_entries[i]).__version__}")
        except:
            logging.info(f"{i}\tunknown")

    try:
        logging.info(f"pygame_sdl_version\t{__import__('pygame').get_sdl_version()}")
    finally:
        pass

    # Get file
    file = open(f"{USER_LOG_DIR}/latest.log")
    send_files = {"tuxemon_log.txt": file}
    r = requests.post(config.log_host_url, files=send_files, headers={"Max-Days": config.log_storage_max_days, "User-Agent": "curl/7.80.0"})
    print(f"Report URL: {r.text}")
    file.close()
    __import__("webbrowser").open_new_tab(r.text)

def popup_send_log_consent():
    """
    Popup requesting consent for sending crash report.
    Returns bool value with the choice.
    """
    title="Tuxemon", 
    text="Sadly, Tuxemon crashed. Do you want to send crash report to the tuxemon team?",
    choices=["yes", "no"]

    tk.Tk().wm_withdraw()
    msgbox = messagebox.askyesno(title=title, message=text)
    return msgbox
