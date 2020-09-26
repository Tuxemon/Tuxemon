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


import os.path

from tuxemon.core.platform import get_config_dir

# tuxemon project root dir
BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# main game and config dir
# TODO: this imports pygame from core.prepare - refactor to avoid this?
USER_GAME_DIR = get_config_dir()

CONFIG_FILE = "tuxemon.cfg"

# config file paths
USER_CONFIG_PATH = os.path.join(USER_GAME_DIR, CONFIG_FILE)
DEFAULT_CONFIG_PATH = os.path.join(BASEDIR, CONFIG_FILE)

# game data dir
USER_GAME_DATA_DIR = os.path.join(USER_GAME_DIR, "data")

# game savegame dir
USER_GAME_SAVE_DIR = os.path.join(USER_GAME_DIR, "saves")

# mods
mods_folder = os.path.normpath(os.path.join(BASEDIR, "..", "mods"))

# action/condition plugins (eventually move out of lib folder)
CONDITIONS_PATH = os.path.join(BASEDIR, "core/event/conditions")
ACTIONS_PATH = os.path.join(BASEDIR, "core/event/actions")

# item effects/conditions
ITEM_EFFECT_PATH = os.path.join(BASEDIR, "core/item/effects")
ITEM_CONDITION_PATH = os.path.join(BASEDIR, "core/item/conditions")
