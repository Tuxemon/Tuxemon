# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import os.path
import sys

from tuxemon import platform

logger = logging.getLogger(__file__)


# LIBDIR is where the tuxemon lib is
LIBDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logger.debug("libdir: %s", LIBDIR)

# BASEDIR is where tuxemon was launched from
BASEDIR = sys.path[0]
logger.debug("basedir: %s", BASEDIR)

# main game and config dir
# TODO: this imports pygame from prepare - refactor to avoid this?
USER_STORAGE_DIR = platform.get_user_storage_dir()
logger.debug("userdir: %s", USER_STORAGE_DIR)

# config file paths
CONFIG_FILE = "tuxemon.cfg"
USER_CONFIG_PATH = os.path.join(USER_STORAGE_DIR, CONFIG_FILE)
logger.debug("user config: %s", USER_CONFIG_PATH)

# game data dir
USER_GAME_DATA_DIR = os.path.join(USER_STORAGE_DIR, "data")
logger.debug("user game data: %s", USER_GAME_DATA_DIR)

# game savegame dir
USER_GAME_SAVE_DIR = os.path.join(USER_STORAGE_DIR, "saves")
logger.debug("save games: %s", USER_GAME_SAVE_DIR)

# game cache dir
CACHE_DIR = os.path.join(USER_STORAGE_DIR, "cache")
logger.debug("cache: %s", CACHE_DIR)

# game lang dir
L18N_MO_FILES = os.path.join(CACHE_DIR, "l18n")
logger.debug("l18: %s", L18N_MO_FILES)

# mods
mods_folder = os.path.normpath(os.path.join(LIBDIR, "..", "mods"))
logger.debug("mods: %s", mods_folder)

# shared locations
system_installed_folders = platform.get_system_storage_dirs()

# action/condition plugins (eventually move out of lib folder)
CONDITIONS_PATH = os.path.join(LIBDIR, "event/conditions")
ACTIONS_PATH = os.path.join(LIBDIR, "event/actions")

# item effects/conditions
ITEM_EFFECT_PATH = os.path.join(LIBDIR, "item/effects")
ITEM_CONDITION_PATH = os.path.join(LIBDIR, "item/conditions")

# technique effects/conditions
TECH_EFFECT_PATH = os.path.join(LIBDIR, "technique/effects")
TECH_CONDITION_PATH = os.path.join(LIBDIR, "technique/conditions")

# condition effects/conditions
COND_EFFECT_PATH = os.path.join(LIBDIR, "condition/effects")
COND_CONDITION_PATH = os.path.join(LIBDIR, "condition/conditions")
