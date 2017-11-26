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
# core.components.config Configuration parser.
#
#
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import pygame

# set default animation to 'out_quint'
from core.components.animation import Animation
Animation.default_transition = 'out_quint'

# read by Config and HeadlessConfig
FILE_DEFAULT = configparser.ConfigParser()
FILE_CONFIG = configparser.ConfigParser()

# customized version of config.get
# tries the user config first, uses the default config if the setting is missing
def config_get(section, setting):
    try:
        return FILE_CONFIG.get(section, setting)
    except configparser.NoOptionError:
        return FILE_DEFAULT.get(section, setting)

class Config(object):
    """Handles loading of the configuration file for the primary game and map editor.

    """
    def __init__(self, file_default = "tuxemon.cfg", file_config = "tuxemon.cfg"):
        FILE_DEFAULT.read(file_default)
        FILE_CONFIG.read(file_config)

        # [display]
        self.resolution_x = config_get("display", "resolution_x")
        self.resolution_y = config_get("display", "resolution_y")
        self.resolution = (int(self.resolution_x), int(self.resolution_y))
        self.splash = config_get("display", "splash")
        self.fullscreen = self.fullscreen_check()
        self.fps = float(config_get("display", "fps"))
        self.show_fps = int(config_get("display", "show_fps"))
        self.scaling = config_get("display", "scaling")
        self.collision_map = config_get("display", "collision_map")
        self.controller_overlay = config_get("display", "controller_overlay")
        self.controller_transparency = int(config_get("display", "controller_transparency"))

        # [sound]
        self.sound_volume = float(config_get("sound", "sound_volume"))
        self.music_volume = float(config_get("sound", "music_volume"))

        # [game]
        self.data = config_get("game", "data")
        self.starting_map = config_get("game", "starting_map")
        self.cli = int(config_get("game", "cli_enabled"))
        self.net_controller_enabled = config_get("game", "net_controller_enabled")
        self.locale = config_get("game", "locale")

        # [player]
        self.player_animation_speed = float(config_get("player", "animation_speed"))
        self.player_npc = config_get("player", "player_npc")

        # [logging]
        self.loggers = config_get("logging", "loggers")
        self.loggers = self.loggers.replace(" ", "").split(",")
        self.debug_logging = config_get("logging", "debug_logging")
        self.debug_level = str(config_get("logging", "debug_level")).lower()

    def fullscreen_check(self):
        """If the fullscreen option is set in our configuration option, return a
        "pygame.FULLSCREEN" object to the game.

        :param: None

        :rtype: pygame.FULLSCREEN
        :returns: pygame.FULLSCREEN object or 0

        """
        if config_get("display", "fullscreen") == "1":
            return pygame.FULLSCREEN
        else:
            return 0

class HeadlessConfig(object):
    """Handles loading of the configuration file for the headless server.
    """
    def __init__(self, file_default = "tuxemon.cfg", file_config = "tuxemon.cfg"):
        FILE_DEFAULT.read(file_default)
        FILE_CONFIG.read(file_config)

        # [game]
        self.cli = int(config_get("game", "cli_enabled"))

        # [logging]
        self.loggers = config_get("logging", "loggers")
        self.loggers = self.loggers.replace(" ", "").split(",")
        self.debug_logging = config_get("logging", "debug_logging")
        self.debug_level = config_get("logging", "debug_level")


