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
# Derek J. Clark <derekjohn.clark@gmail.com>
#
#
# core.states.start Handles the splash screen and start menu.
#
#

import logging
import pygame
import os
import sys
import pprint
import random

from .. import tools, prepare
from ..components import pyganim
from ..components import db
from ..components import fusion
from ..components.menu import pc_menu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.start successfully imported")

class PC(tools._State):
    """The module responsible for the splash screen and start menu.

    :param game: The scene manager object that contains all the game's variables.
    :type game: core.tools.Control

    """

    def __init__(self, game):
        # Initiate our common state properties.
        tools._State.__init__(self)
    
        from ..components import menu
        
        # Provide an instance of the scene manager to this scene.
        self.game = game            # The scene manger object
        self.previous_menu = None
        self.menu_blocking = True
        
        scale = prepare.SCALE
        
        self.pc_menu = pc_menu.PCMenu(self.game.screen, prepare.SCREEN_SIZE, self.game)
        self.pc_menu.size_x= int(prepare.SCREEN_SIZE[0]*0.9)
        self.pc_menu.size_y= int(prepare.SCREEN_SIZE[1]*0.9)
        self.pc_menu.pos_x = (prepare.SCREEN_SIZE[0] / 2) - (self.pc_menu.size_x/2)
        self.pc_menu.pos_y = (prepare.SCREEN_SIZE[1] / 2) - (self.pc_menu.size_y/2)
        self.pc_menu.interactable = True
        
        # This menu is just used to display a message that a particular
        # feature is not yet implemented.
        self.multiplayer_menu = pc_menu.Multiplayer_Menu(self.game.screen,
                                              prepare.SCREEN_SIZE,
                                              self.game)
        self.multiplayer_menu.size_x = int(prepare.SCREEN_SIZE[0] / 1.5)
        self.multiplayer_menu.size_y = prepare.SCREEN_SIZE[1] / 5
        self.multiplayer_menu.pos_x = (prepare.SCREEN_SIZE[0] / 2) - \
            (self.multiplayer_menu.size_x / 2)
        self.multiplayer_menu.pos_y = (prepare.SCREEN_SIZE[1] / 2) - \
            (self.multiplayer_menu.size_y / 2)
        self.multiplayer_menu.visible = False
        self.multiplayer_menu.interactable = False
        
        self.multiplayer_join_menu = pc_menu.Multiplayer_Join_Menu(self.game.screen,
                                              prepare.SCREEN_SIZE,
                                              self.game)
        self.multiplayer_join_menu.size_x = int(prepare.SCREEN_SIZE[0] / 1.5)
        self.multiplayer_join_menu.size_y = prepare.SCREEN_SIZE[1] / 5
        self.multiplayer_join_menu.pos_x = (prepare.SCREEN_SIZE[0] / 2) - \
            (self.multiplayer_menu.size_x / 2)
        self.multiplayer_join_menu.pos_y = (prepare.SCREEN_SIZE[1] / 2) - \
            (self.multiplayer_menu.size_y / 2)
        self.multiplayer_join_menu.visible = False
        self.multiplayer_join_menu.interactable = False
        
        
        self.menus = [self.pc_menu, self.multiplayer_menu, self.multiplayer_join_menu]
        
        
        for menu in self.menus:
            menu.scale = scale    # Set the scale of the menu.
            menu.set_font(size=menu.font_size * scale,
                          font=prepare.BASEDIR + "resources/font/PressStart2P.ttf",
                          color=(10, 10, 10),
                          spacing=menu.font_size * scale)

            # Scale the selection arrow image based on our game's scale.
            menu.arrow = pygame.transform.scale(
                menu.arrow,
                (menu.arrow.get_width() * scale,
                 menu.arrow.get_height() * scale))

            # Scale the border images based on our game's scale.
            for key, border in menu.border.items():
                menu.border[key] = pygame.transform.scale(
                    border,
                    (border.get_width() * scale,
                     border.get_height() * scale))

        

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


    def cleanup(self):
        """Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.

        :param None:

        :rtype: Dictionary
        :returns: Persist dictionary of variables.

        """

        self.done = False
        return self.persist


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
        
        if self.multiplayer_join_menu.interactable:
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
                
            
    
    


