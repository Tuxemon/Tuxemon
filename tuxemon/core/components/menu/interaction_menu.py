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
# core.components.menu.interaction_menu
#
"""This module contains the Interaction Menu
"""
import pygame
from core import prepare
from core.components.menu import Menu

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer

class InteractionMenu(Menu):

    def __init__(self, screen, resolution, game, name="Interaction Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.first_run = True
        self.save = False
        self.state = "closed"
        self.visible = False
        
        self.menu_select_sound = mixer.Sound(
            prepare.BASEDIR + "resources/sounds/interface/50561__broumbroum__sf3-sfx-menu-select.ogg")


    def get_event(self, event, game=None):
        
        interaction = None
        
        if self.selected_menu_item == 0 and len(self.menu_items) > 1:
            self.selected_menu_item = 1
            
        if len(self.menu_items) > 0:
            self.line_spacing = (self.size_y / len(self.menu_items)) - self.font_size

        if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > len(self.menu_items):
                self.selected_menu_item = 1

            self.menu_select_sound.play()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 1:
                self.selected_menu_item = len(self.menu_items) -1

            self.menu_select_sound.play()

        # If the player presses Enter while a menu item is selected
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.menu_select_sound.play()

            if self.menu_items[self.selected_menu_item] == "DUEL":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
#                 if self.game.game.isclient or self.game.game.ishost:
#                     self.game.game.client.player_interact(self.player, "DUEL")
                    
            elif self.menu_items[self.selected_menu_item] == "TRADE":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
                
            elif self.menu_items[self.selected_menu_item] == "Accept" or self.menu_items[self.selected_menu_item] == "Decline":
                response = self.menu_items[self.selected_menu_item]
                self.game.game.client.player_interact(self.player, self.interaction, "CLIENT_RESPONSE", response)                    
                if self.interaction == "DUEL":
                    if response == "Accept":
                        self.game.wants_duel = True
                    elif response == "Decline":
                        self.game.wants_duel = False
                


