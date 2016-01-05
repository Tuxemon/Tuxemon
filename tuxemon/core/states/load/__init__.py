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
# core.states.start Handles the splash screen and start menu(Not anymore! - B).
#
"""This module contains the Start state.
"""
import logging
import pygame

from core import prepare
from core import state
from core.components.menu import load_menu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.start successfully imported")


class LOAD(state.State):
    """ The state responsible for the and start menu.
    """

    def startup(self, params=None):
        # Provide an instance of the scene manager to this scene.
        self.previous_menu = None
        self.menu_blocking = True

        # Provide access to the screen surface
        self.screen = self.game.screen
        self.screen_rect = prepare.SCREEN_RECT

        # Set the native tile size so we know how much to scale
        self.tile_size = prepare.TILE_SIZE

        # Set the status icon size so we know how much to scale
        self.icon_size = prepare.ICON_SIZE

        # Get the screen's resolution
        self.resolution = prepare.SCREEN_SIZE

        # Native resolution is similar to the old gameboy resolution. This is
        # used for scaling.
        self.native_resolution = prepare.NATIVE_RESOLUTION
        self.scale = prepare.SCALE

        # Load menu.
        self.load_menu = load_menu.LoadMenu(self.screen,
                                            self.resolution,
                                            self.game,
                                            "Load_Menu")
        self.load_menu.visible = True
        self.load_menu.interactable = True
        self.load_menu.size_ratio = [0.7, 0.7]

        self.menus = [self.load_menu]

        for menu in self.menus:
            menu.scale = self.scale    # Set the scale of the menu.
            menu.set_font(size=menu.font_size * self.scale,
                          font=prepare.BASEDIR +
                          "resources/font/PressStart2P.ttf",
                          color=(10, 10, 10),
                          spacing=menu.font_size * self.scale)

            # Scale the selection arrow image based on our game's scale.
            menu.arrow = pygame.transform.scale(
                menu.arrow,
                (menu.arrow.get_width() * self.scale,
                 menu.arrow.get_height() * self.scale))

            # Scale the border images based on our game's scale.
            for key, border in menu.border.items():
                menu.border[key] = pygame.transform.scale(
                    border,
                    (border.get_width() * self.scale,
                     border.get_height() * self.scale))

            # Set the menu size.

            menu.size_x = int(self.resolution[0] * menu.size_ratio[0])
            menu.size_y = int(self.resolution[1] * menu.size_ratio[1])
            menu.pos_x = (self.resolution[0] / 2) - (menu.size_x/2)
            menu.pos_y = (self.resolution[1] / 2) - (menu.size_y/2)

    def update(self, time_delta):
        """Update function for state.

        :type surface: pygame.Surface
        :rtype: None
        :returns: None

        """
        pass

    def get_event(self, event):
        """Processes events that were passed from the main event loop.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        if self.load_menu.interactable:
            self.load_menu.get_event(event)

    def draw(self, surface):
        """Draws the start screen to the screen.

        :param surface:
        :param Surface: Surface to draw to

        :type Surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        if self.load_menu.visible:
            self.load_menu.draw()
