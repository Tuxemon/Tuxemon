# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import sys
from pathlib import Path

from tuxemon.platform import platform

logger = logging.getLogger(__name__)


# --- Core Game Paths ---

# LIBDIR is where the tuxemon lib is
LIBDIR = Path(__file__).resolve().parent.parent
logger.debug(f"libdir: {LIBDIR}")

ROOT_PACKAGE_NAME = LIBDIR.name
logger.debug(f"root package name: {ROOT_PACKAGE_NAME}")

# BASEDIR is where tuxemon was launched from
BASEDIR = Path(sys.path[0]).resolve()
logger.debug(f"basedir: {BASEDIR}")

# mods
# For cx_freeze builds, LIBDIR is in lib/tuxemon, so we need to go up two levels
# For normal installs, LIBDIR is in tuxemon, so we go up one level
if hasattr(sys, "frozen") and sys.frozen:
    # cx_freeze build: exe.win-amd64-3.12\lib\tuxemon -> exe.win-amd64-3.12\mods
    mods_folder = (LIBDIR.parent.parent / "mods").resolve()
else:
    # normal install: tuxemon -> mods
    mods_folder = (LIBDIR.parent / "mods").resolve()
logger.debug(f"mods: {mods_folder}")

# mods subfolders
mods_subfolders = [f.name for f in mods_folder.iterdir() if f.is_dir()]
logger.debug(f"Mods subfolders: {mods_subfolders}")

PLUGIN_CATEGORY_MAP = {
    "event_actions": ("event", "actions"),
    "event_conditions": ("event", "conditions"),
    "event_behaviors": ("event", "behaviors"),
    "core_effects": ("core", "effects"),
    "core_conditions": ("core", "conditions"),
}
PLUGIN_INCLUDE_PATTERNS = [
    ".".join(parts) for parts in PLUGIN_CATEGORY_MAP.values()
]

CONDITIONS_PATH = LIBDIR.joinpath(*PLUGIN_CATEGORY_MAP["event_conditions"])
ACTIONS_PATH = LIBDIR.joinpath(*PLUGIN_CATEGORY_MAP["event_actions"])
BEHAVS_PATH = LIBDIR.joinpath(*PLUGIN_CATEGORY_MAP["event_behaviors"])

CORE_EFFECT_PATH = LIBDIR.joinpath(*PLUGIN_CATEGORY_MAP["core_effects"])
CORE_CONDITION_PATH = LIBDIR.joinpath(*PLUGIN_CATEGORY_MAP["core_conditions"])

# --- User Data Paths ---

# main game and config dir
# Ensure this doesn't depend on pygame
USER_STORAGE_DIR = platform.user_storage.user_dir()
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

# game recording dir
USER_RECORDING_DIR = USER_STORAGE_DIR / "recordings"
logger.debug(f"recordings: {USER_RECORDING_DIR}")

# game cache dir
CACHE_DIR = USER_STORAGE_DIR / "cache"
logger.debug(f"cache: {CACHE_DIR}")

# game lang dir
L18N_MO_FILES = CACHE_DIR / "l18n"
logger.debug(f"l18: {L18N_MO_FILES}")

# --- System Paths ---

# shared locations
system_installed_folders = [
    h.path for h in platform.system_storage.system_dirs() if h.path is not None
]
logger.debug(f"system folders: {system_installed_folders}")


# --- Methods ---


def get_active_mod_paths() -> list[Path]:
    """
    Scans the mods folder and returns a list of paths to all active mod directories.
    """
    active_mod_paths = []
    # Iterate through all subdirectories in the mods folder
    for mod_dir in mods_folder.iterdir():
        # Check if the entry is a directory and not a hidden or special folder
        if mod_dir.is_dir() and not mod_dir.name.startswith((".", "__")):
            active_mod_paths.append(mod_dir)
    return active_mod_paths


def get_plugin_paths(
    base_path: Path, category: str, subfolder: str | None = None
) -> list[Path]:
    """
    Return a list of plugin directories from core and active mods for the given category and optional subfolder.
    """
    plugin_paths = [base_path]
    for mod_path in get_active_mod_paths():
        mod_plugin_path = mod_path / (subfolder or "") / category
        if mod_plugin_path.is_dir():
            plugin_paths.append(mod_plugin_path)
    return plugin_paths


def get_mod_name_from_path(file_path: Path) -> str | None:
    """
    Extracts the mod name from a given file path.

    The mod name is assumed to be the directory immediately following
    the "mods" directory.
    """
    try:
        mod_index = file_path.parts.index("mods")
        if mod_index + 1 < len(file_path.parts):
            return file_path.parts[mod_index + 1]
        else:
            logger.warning(f"Path ends after 'mods' folder: {file_path}")
            return None
    except ValueError:
        logger.error(f"The path does not contain a 'mods' folder: {file_path}")
        return None
    except IndexError:
        logger.error(
            f"Path is too short to contain a mod name after 'mods': {file_path}"
        )
        return None
