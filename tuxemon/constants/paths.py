# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import sys
from pathlib import Path

from tuxemon.platform import get_system_storage_dirs, get_user_storage_dir

logger = logging.getLogger(__name__)

PLUGIN_INCLUDE_PATTERNS = [
    "event.actions",
    "event.conditions",
    "core.effects",
    "core.conditions",
]

# --- Core Game Paths ---

# LIBDIR is where the tuxemon lib is
LIBDIR = Path(__file__).resolve().parent.parent
logger.debug(f"libdir: {LIBDIR}")

# BASEDIR is where tuxemon was launched from
BASEDIR = Path(sys.path[0]).resolve()
logger.debug(f"basedir: {BASEDIR}")

# mods
mods_folder = (LIBDIR.parent / "mods").resolve()
logger.debug(f"mods: {mods_folder}")

# mods subfolders
mods_subfolders = [f.name for f in mods_folder.iterdir() if f.is_dir()]
logger.debug(f"Mods subfolders: {mods_subfolders}")

# action/condition plugins (eventually move out of lib folder)
CONDITIONS_PATH = LIBDIR / "event" / "conditions"
ACTIONS_PATH = LIBDIR / "event" / "actions"

CORE_EFFECT_PATH = LIBDIR / "core" / "effects"
CORE_CONDITION_PATH = LIBDIR / "core" / "conditions"

# --- User Data Paths ---

# main game and config dir
# Ensure this doesn't depend on pygame
USER_STORAGE_DIR = get_user_storage_dir()
logger.debug(f"userdir: {USER_STORAGE_DIR}")

# config file paths
CONFIG_FILE = "tuxemon.yaml"
USER_CONFIG_PATH = USER_STORAGE_DIR / CONFIG_FILE
logger.debug(f"user config: {USER_CONFIG_PATH}")

# game data dir
USER_GAME_DATA_DIR = USER_STORAGE_DIR / "data"
logger.debug(f"user game data: {USER_GAME_DATA_DIR}")

# game savegame dir
USER_GAME_SAVE_DIR = USER_STORAGE_DIR / "saves"
logger.debug(f"save games: {USER_GAME_SAVE_DIR}")

# game cache dir
CACHE_DIR = USER_STORAGE_DIR / "cache"
logger.debug(f"cache: {CACHE_DIR}")

# game lang dir
L18N_MO_FILES = CACHE_DIR / "l18n"
logger.debug(f"l18: {L18N_MO_FILES}")

# --- System Paths ---

# shared locations
system_installed_folders = [
    path.resolve() for path in get_system_storage_dirs()
]
logger.debug(f"system folders: {system_installed_folders}")
