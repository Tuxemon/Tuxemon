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
# core.controller Controller overlay functions for mobile.
#
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import pygame

from tuxemon.compat import Rect
from tuxemon.core import graphics
from tuxemon.core import screen

logger = logging.getLogger(__name__)


class ControllerOverlay(object):
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
        from tuxemon.core import prepare
        self.dpad["surface"] = graphics.load_and_scale("gfx/d-pad.png")
        self.dpad["position"] = (0, prepare.SCREEN_SIZE[1] - self.dpad["surface"].get_height())

        # Create the collision rectangle objects for the dpad so we can see if we're pressing a button
        self.dpad["rect"] = {}
        self.dpad["rect"]["up"] = Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /3),
            self.dpad["position"][1],                      # Rectangle position_y
            self.dpad["surface"].get_width() /3,           # Rectangle size_x
            self.dpad["surface"].get_height() /2)          # Rectangle size_y
        self.dpad["rect"]["down"] = Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /3),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /2),
            self.dpad["surface"].get_width() /3,
            self.dpad["surface"].get_height() /2)
        self.dpad["rect"]["left"] = Rect(self.dpad["position"][0],
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /3),
            self.dpad["surface"].get_width() /2,
            self.dpad["surface"].get_height() /3)
        self.dpad["rect"]["right"] = Rect(self.dpad["position"][0] + (self.dpad["surface"].get_width() /2),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() /3),
            self.dpad["surface"].get_width() /2,
            self.dpad["surface"].get_height() /3)

        # Create the buttons
        self.a_button = {}
        self.a_button["surface"] = graphics.load_and_scale("gfx/a-button.png")
        self.a_button["position"] = (prepare.SCREEN_SIZE[0] - int( self.a_button["surface"].get_width() * 1.0 ),
            (self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2) - (self.a_button["surface"].get_height() / 2)))
        self.a_button["rect"] = Rect(
            self.a_button["position"][0], self.a_button["position"][1],
            self.a_button["surface"].get_width(),
            self.a_button["surface"].get_height())

        self.b_button = {}
        self.b_button["surface"] = graphics.load_and_scale("gfx/b-button.png")
        self.b_button["position"] = (prepare.SCREEN_SIZE[0] - int( self.b_button["surface"].get_width() * 2.1 ),
            (self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2) - (self.b_button["surface"].get_height() / 2)))
        self.b_button["rect"] = Rect(
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
