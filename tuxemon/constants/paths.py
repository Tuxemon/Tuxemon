# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import os
import sys

from tuxemon import platform

logger = logging.getLogger(__name__)

PLUGIN_INCLUDE_PATTERNS = [
    "event.actions",
    "event.conditions",
    "item.effects",
    "item.conditions",
    "technique.effects",
    "technique.conditions",
    "status.effects",
    "status.conditions",
]

# --- Core Game Paths ---

# LIBDIR is where the tuxemon lib is
LIBDIR = os.path.normpath(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)
logger.debug(f"libdir: {LIBDIR}")

# BASEDIR is where tuxemon was launched from
BASEDIR = os.path.normpath(sys.path[0])
logger.debug(f"basedir: {BASEDIR}")

# mods
mods_folder = os.path.normpath(os.path.join(LIBDIR, "..", "mods"))
logger.debug(f"mods: {mods_folder}")

# action/condition plugins (eventually move out of lib folder)
CONDITIONS_PATH = os.path.normpath(os.path.join(LIBDIR, "event/conditions"))
ACTIONS_PATH = os.path.normpath(os.path.join(LIBDIR, "event/actions"))

ITEM_EFFECT_PATH = os.path.normpath(os.path.join(LIBDIR, "item/effects"))
ITEM_CONDITION_PATH = os.path.normpath(os.path.join(LIBDIR, "item/conditions"))

TECH_EFFECT_PATH = os.path.normpath(os.path.join(LIBDIR, "technique/effects"))
TECH_CONDITION_PATH = os.path.normpath(
    os.path.join(LIBDIR, "technique/conditions")
)

STATUS_EFFECT_PATH = os.path.normpath(os.path.join(LIBDIR, "status/effects"))
STATUS_CONDITION_PATH = os.path.normpath(
    os.path.join(LIBDIR, "status/conditions")
)

# --- User Data Paths ---

# main game and config dir
USER_STORAGE_DIR = (
    platform.get_user_storage_dir()
)  # Ensure this doesn't depend on pygame
logger.debug(f"userdir: {USER_STORAGE_DIR}")

# config file paths
CONFIG_FILE = "tuxemon.cfg"
USER_CONFIG_PATH = os.path.normpath(
    os.path.join(USER_STORAGE_DIR, CONFIG_FILE)
)
logger.debug(f"user config: {USER_CONFIG_PATH}")

# game data dir
USER_GAME_DATA_DIR = os.path.normpath(os.path.join(USER_STORAGE_DIR, "data"))
logger.debug(f"user game data: {USER_GAME_DATA_DIR}")

# game savegame dir
USER_GAME_SAVE_DIR = os.path.normpath(os.path.join(USER_STORAGE_DIR, "saves"))
logger.debug(f"save games: {USER_GAME_SAVE_DIR}")

# game cache dir
CACHE_DIR = os.path.normpath(os.path.join(USER_STORAGE_DIR, "cache"))
logger.debug(f"cache: {CACHE_DIR}")

# game lang dir
L18N_MO_FILES = os.path.normpath(os.path.join(CACHE_DIR, "l18n"))
logger.debug(f"l18: {L18N_MO_FILES}")

# --- System Paths ---

# shared locations
system_installed_folders = [
    os.path.normpath(path) for path in platform.get_system_storage_dirs()
]
logger.debug(f"system folders: {system_installed_folders}")
