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
# core.components.controller Controller overlay functions for mobile.
#
#

import logging
import pygame
from . import screen
from core import tools

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class Controller(object):
    """Handles the controller overlay functionality for mobile versions of the game. This includes
    detecting screen touches of on-screen buttons so they can be translated to keystrokes as well
    as drawing the controller overlay itself.

    .. image:: images/menu/controller_overlay01.png

    :param game: The main game object that contains all the game’s variables.
    :type game: tuxemon.Game

    """
    def __init__(self, game):
        self.game = game
        self.dpad = {}

    def load(self):
        from core import prepare
        self.dpad["surface"] = tools.load_and_scale("gfx/d-pad.png")
        self.dpad["position"] = (0, prepare.SCREEN_SIZE[1] - self.dpad["surface"].get_height() )

        # Create the collision rectangle objects for the dpad so we can see if we're pressing a button
        self.dpad["rect"] = {}
        self.dpad["rect"]["up"] = pygame.Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /3),
            self.dpad["position"][1],                      # Rectangle position_y
            self.dpad["surface"].get_width() /3,           # Rectangle size_x
            self.dpad["surface"].get_height() /2)          # Rectangle size_y
        self.dpad["rect"]["down"] = pygame.Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /3),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /2),
            self.dpad["surface"].get_width() /3,
            self.dpad["surface"].get_height() /2)
        self.dpad["rect"]["left"] = pygame.Rect(self.dpad["position"][0],
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /3),
            self.dpad["surface"].get_width() /2,
            self.dpad["surface"].get_height() /3)
        self.dpad["rect"]["right"] = pygame.Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /2),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /3),
            self.dpad["surface"].get_width() /2,
            self.dpad["surface"].get_height() /3)

        # Create the buttons
        self.a_button = {}
        self.a_button["surface"] = tools.load_and_scale("gfx/a-button.png")
        self.a_button["position"] = (prepare.SCREEN_SIZE[0] - int( self.a_button["surface"].get_width() * 1.0 ),
            (self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2) - (self.a_button["surface"].get_height() / 2)))
        self.a_button["rect"] = pygame.Rect(
            self.a_button["position"][0], self.a_button["position"][1],
            self.a_button["surface"].get_width(),
            self.a_button["surface"].get_height())

        self.b_button = {}
        self.b_button["surface"] = tools.load_and_scale("gfx/b-button.png")
        self.b_button["position"] = (prepare.SCREEN_SIZE[0] - int( self.b_button["surface"].get_width() * 2.1 ),
            (self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2) - (self.b_button["surface"].get_height() / 2)))
        self.b_button["rect"] = pygame.Rect(
            self.b_button["position"][0],
            self.b_button["position"][1],
            self.b_button["surface"].get_width(),
            self.b_button["surface"].get_height())


    def draw(self, game):
        """Draws the controller overlay to the screen.

        :param game: The main game object that contains all the game’s variables.
        :type game: tuxemon.Game

        :rtype: None
        :returns: None

        """
        screen.blit_alpha(game.screen,
                          self.dpad["surface"],
                          self.dpad["position"],
                          game.config.controller_transparency)
        screen.blit_alpha(game.screen,
                          self.a_button["surface"],
                          self.a_button["position"],
                          game.config.controller_transparency)
        screen.blit_alpha(game.screen,
                          self.b_button["surface"],
                          self.b_button["position"],
                          game.config.controller_transparency)
