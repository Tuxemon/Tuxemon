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
# Derek Clark <derekjohn.clark@gmail.com>
#
# core.components.states
#
"""This module contains the PC state.
"""
import logging
import pygame

from core import prepare
from core import state
from core.components.menu import pc_menu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.start successfully imported")


class PC(state.State):
    """The module responsible in game settings.

    :param game: The scene manager object that contains all the game's variables.
    :type game: core.tools.Control

    """

    def __init__(self, game):
        # Initiate our common state properties.
        state.State.__init__(self)

        from core.components import menu

        # Provide an instance of the scene manager to this scene.
        self.game = game            # The scene manger object
        self.previous_menu = None
        self.menu_blocking = True

         # Provide access to the screen surface
        self.screen = game.screen
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

        # Main PC menu.
        self.pc_menu = pc_menu.PCMenu(self.screen,
                                      self.resolution,
                                      self.game)

        self.pc_menu.interactable = True
        self.pc_menu.size_ratio = [0.8, 0.3]

        # Main multiplayer menu.
        self.multiplayer_menu = pc_menu.Multiplayer_Menu(self.screen,
                                                         self.resolution,
                                                         self.game)
        self.multiplayer_menu.visible = False
        self.multiplayer_menu.interactable = False
        self.multiplayer_menu.size_ratio = [0.7, 0.25]

        # Join a multiplayer game menu.
        self.multiplayer_join_menu = pc_menu.Multiplayer_Join_Menu(self.screen,
                                                                   self.resolution,
                                                                   self.game)
        self.multiplayer_join_menu.visible = False
        self.multiplayer_join_menu.interactable = False
        self.multiplayer_join_menu.size_ratio = [0.6, 0.2]

        # Successfully joined a multiplayer game menu.
        self.multiplayer_join_success_menu = pc_menu.Multiplayer_Join_Success_Menu(self.screen,
                                                                                   self.resolution,
                                                                                   self.game)
        self.multiplayer_join_success_menu.visible = False
        self.multiplayer_join_success_menu.interactable = False
        self.multiplayer_join_success_menu.size_ratio = [0.6, 0.2]

        # Successfully host a game menu.
        self.multiplayer_host_menu = pc_menu.Multiplayer_Host_Menu(self.screen,
                                                                   self.resolution,
                                                                   self.game)
        self.multiplayer_host_menu.visible = False
        self.multiplayer_host_menu.interactable = False
        self.multiplayer_host_menu.size_ratio = [0.6, 0.2]

        self.menus = [self.pc_menu,
                      self.multiplayer_menu,
                      self.multiplayer_join_menu,
                      self.multiplayer_join_success_menu,
                      self.multiplayer_host_menu
                      ]

        for menu in self.menus:
            menu.scale = self.scale    # Set the scale of the menu.
            menu.set_font(size=menu.font_size * self.scale,
                          font=prepare.BASEDIR + "resources/font/PressStart2P.ttf",
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
            menu.size_x= int(self.resolution[0] * menu.size_ratio[0])
            menu.size_y= int(self.resolution[1] * menu.size_ratio[1])
            menu.pos_x = (self.resolution[0] / 2) - (menu.size_x/2)
            menu.pos_y = (self.resolution[1] / 2) - (menu.size_y/2)


    def startup(self, current_time, persistant):
        """Perform startup tasks when we switch to this scene.

        :param current_time: Current time passed.
        :param persistant: Keep a dictionary of optional persistant variables.

        :type current_time: Integer
        :type persistant: Dictionary

        :rtype: None
        :returns: None


        **Examples:**

        >>> current_time
        2895
        >>> persistant
        {}

        """

        self.persist = persistant
        self.start_time = current_time


    def update(self, screen, keys, current_time, time_delta):
        """Update function for state.

        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>> surface
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """

        self.draw()


    def get_event(self, event):
        """Processes events that were passed from the main event loop.
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        if self.multiplayer_join_success_menu.interactable:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.get_menu_event(self.multiplayer_join_success_menu, event)

        elif self.multiplayer_host_menu.interactable:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.get_menu_event(self.multiplayer_host_menu, event)

        elif self.multiplayer_join_menu.interactable:
            self.game.get_menu_event(self.multiplayer_join_menu, event)

        elif self.multiplayer_menu.interactable:
            self.game.get_menu_event(self.multiplayer_menu, event)

        elif self.pc_menu.interactable:
            self.game.get_menu_event(self.pc_menu, event)


    def draw(self):
        """Draws the start screen to the screen.

        :param None:
        :type None:

        :rtype: None
        :returns: None

        """

        self.game.screen.fill((15, 15, 15))
        self.pc_menu.draw()
        self.pc_menu.draw_textItem(
                ["MULTIPLAYER", "LOG OFF"])


        if self.multiplayer_menu.visible:
            self.multiplayer_menu.draw()
            self.multiplayer_menu.draw_textItem(
                ["JOIN", "HOST"])


        if self.multiplayer_join_menu.visible:
            self.multiplayer_join_menu.draw()
            self.multiplayer_join_menu.draw_textItem(self.game.client.server_list)

            # If no options are selected because there were no items when the menu was populated,
            # and there are items in the list to select, set the selected item to the top of the list.
            if self.multiplayer_join_menu.selected_menu_item <= 0 and \
            len(self.multiplayer_join_menu.menu_items) > 0:
                self.multiplayer_join_menu.selected_menu_item = 0

        if self.multiplayer_join_success_menu.visible:
            self.multiplayer_join_success_menu.draw()
            self.multiplayer_join_success_menu.draw_textItem(self.multiplayer_join_success_menu.text)

        if self.multiplayer_host_menu.visible:
            self.multiplayer_host_menu.draw()
            self.multiplayer_host_menu.draw_textItem(self.multiplayer_host_menu.text)





