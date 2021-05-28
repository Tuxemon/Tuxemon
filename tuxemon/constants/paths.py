#
# Tuxemon
# Copyright (C) 2018, Andy Mender <andymenderunix@gmail.com>
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
# Andy Mender <andymenderunix@gmail.com>
#
#
# constants.paths - Central store for local file paths
#
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
