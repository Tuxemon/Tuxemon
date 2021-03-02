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
# core.constants.paths - Central store for local file paths
#
import logging
import os.path
import sys

from tuxemon.core.platform import get_config_dir

logger = logging.getLogger(__file__)


# LIBDIR is where the tuxemon lib is
LIBDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logger.debug("libdir: %s", LIBDIR)

# BASEDIR is where tuxemon was launched from
BASEDIR = sys.path[0]
logger.debug("basedir: %s", BASEDIR)

# main game and config dir
# TODO: this imports pygame from core.prepare - refactor to avoid this?
USER_GAME_DIR = get_config_dir()
logger.debug("userdir: %s", USER_GAME_DIR)

CONFIG_FILE = "tuxemon.cfg"

# config file paths
USER_CONFIG_PATH = os.path.join(USER_GAME_DIR, CONFIG_FILE)
logger.debug("user config: %s", USER_CONFIG_PATH)

DEFAULT_CONFIG_PATH = os.path.join(BASEDIR, CONFIG_FILE)
logger.debug("default config: %s", DEFAULT_CONFIG_PATH)

# game data dir
USER_GAME_DATA_DIR = os.path.join(USER_GAME_DIR, "data")
logger.debug("user game data: %s", USER_GAME_DATA_DIR)

# game savegame dir
USER_GAME_SAVE_DIR = os.path.join(USER_GAME_DIR, "saves")
logger.debug("save games: %s", USER_GAME_SAVE_DIR)

# game savegame dir
CACHE_DIR = os.path.join(USER_GAME_DIR, "cache")
logger.debug("cache: %s", CACHE_DIR)

# game savegame dir
L18N_MO_FILES = os.path.join(CACHE_DIR, "l18n")
logger.debug("l18: %s", L18N_MO_FILES)

# mods
mods_folder = os.path.normpath(os.path.join(LIBDIR, "..", "mods"))
logger.debug("mods: %s", mods_folder)

# shared locations
system_installed_folders = [
    "/user/share/tuxemon/",  # debian
]


def guess_android():
    # this is a hack.
    global system_installed_folders
    from tuxemon.core import platform
    if platform.android:
        system_installed_folders.clear()
        system_installed_folders.append(platform.get_config_dir())


guess_android()

# action/condition plugins (eventually move out of lib folder)
CONDITIONS_PATH = os.path.join(LIBDIR, "core/event/conditions")
ACTIONS_PATH = os.path.join(LIBDIR, "core/event/actions")

# item effects/conditions
ITEM_EFFECT_PATH = os.path.join(LIBDIR, "core/item/effects")
ITEM_CONDITION_PATH = os.path.join(LIBDIR, "core/item/conditions")
