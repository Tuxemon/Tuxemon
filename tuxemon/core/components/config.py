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


class Config(object):
    """Handles loading of the configuration file for the primary game and map editor.

    """
    def __init__(self, file="tuxemon.cfg"):
        self.config = configparser.ConfigParser()
        self.config.read(file)

        self.resolution_x = self.config.get("display", "resolution_x")
        self.resolution_y = self.config.get("display", "resolution_y")
        self.resolution = (int(self.resolution_x), int(self.resolution_y))

        self.splash = self.config.get("display", "splash")

        self.fullscreen = self.fullscreen_check()
        self.scaling = self.config.get("display", "scaling")
        self.fps = int(self.config.get("display", "fps"))
        self.collision_map = self.config.get("display", "collision_map")

        self.controller_overlay = self.config.get("display", "controller_overlay")
        self.controller_transparency = int(self.config.get("display", "controller_transparency"))

        self.starting_map = self.config.get("game", "starting_map")
        self.starting_position = [int(self.config.get("game", "starting_position_x")),
                                  int(self.config.get("game", "starting_position_y"))]
        self.cli = int(self.config.get("game", "cli_enabled"))
        self.net_controller_enabled = self.config.get("game", "net_controller_enabled")

        self.player_animation_speed = float(self.config.get("player", "animation_speed"))

        self.debug_logging = self.config.get("logging", "debug_logging")
        self.debug_level = str(self.config.get("logging", "debug_level")).lower()
        self.loggers = self.config.get("logging", "loggers")
        self.loggers = self.loggers.replace(" ", "").split(",")

    def fullscreen_check(self):
        """If the fullscreen option is set in our configuration option, return a
        "pygame.FULLSCREEN" object to the game.

        :param: None

        :rtype: pygame.FULLSCREEN
        :returns: pygame.FULLSCREEN object or 0

        """
        if self.config.get("display", "fullscreen") == "1":
            return pygame.FULLSCREEN
        else:
            return 0


class HeadlessConfig(object):
    """Handles loading of the configuration file for the headless server.
    """
    def __init__(self, file="tuxemon.cfg"):
        self.config = configparser.ConfigParser()
        self.config.read(file)

        self.cli = int(self.config.get("game", "cli_enabled"))

        self.debug_logging = self.config.get("logging", "debug_logging")
        self.debug_level = self.config.get("logging", "debug_level")
        self.loggers = self.config.get("logging", "loggers")
        self.loggers = self.loggers.replace(" ", "").split(",")


