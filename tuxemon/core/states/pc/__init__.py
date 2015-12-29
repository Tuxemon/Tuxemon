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
from core.components import networking

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.successfully imported")


class PC(state.State):
    """ The state responsible in game settings.
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

        # Main PC menu.
        self.pc_menu = pc_menu.PCMenu(self.screen,
                                      self.resolution,
                                      self.game)

        self.pc_menu.interactable = True
        self.pc_menu.size_ratio = [0.8, 0.3]

        # Monster menu
        self.monster_menu = pc_menu.Player_Menu(self.screen,
                                                self.resolution,
                                                self.game,
                                                "PLAYER_MONS")
        self.monster_menu.visible = False
        self.monster_menu.interactable = False
        self.monster_menu.size_ratio = [0.5, 0.8]

        # Item menu
        self.item_menu = pc_menu.Player_Menu(self.screen,
                                             self.resolution,
                                             self.game,
                                             "PLAYER_ITEMS")
        self.item_menu.visible = False
        self.item_menu.interactable = False
        self.item_menu.size_ratio = [0.5, 0.8]

        # Storage Monster menu
        self.store_monster_menu = pc_menu.Storage_Menu(self.screen,
                                                       self.resolution,
                                                       self.game,
                                                       "STORE_MONS")

        self.monster_menu.add_child(self.store_monster_menu)
        self.store_monster_menu.add_child(self.monster_menu)
        self.store_monster_menu.visible = False
        self.store_monster_menu.interactable = False
        self.store_monster_menu.size_ratio = [0.5, 0.8]

        # Storage Item menu
        self.store_item_menu = pc_menu.Storage_Menu(self.screen,
                                                    self.resolution,
                                                    self.game,
                                                    "STORE_ITEMS")
        self.item_menu.add_child(self.store_item_menu)
        self.store_item_menu.add_child(self.item_menu)
        self.store_item_menu.visible = False
        self.store_item_menu.interactable = False
        self.store_item_menu.size_ratio = [0.5, 0.8]



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

        # Enter IP adress "menu"
        self.multiplayer_join_enter_ip_menu = pc_menu.Multiplayer_Join_Enter_IP_Menu(self.screen,
                                                                   self.resolution,
                                                                   self.game)
        self.multiplayer_join_enter_ip_menu.visible = False
        self.multiplayer_join_enter_ip_menu.interactable = False
        self.multiplayer_join_enter_ip_menu.size_ratio = [0.6, 0.2]

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
                      self.monster_menu,
                      self.item_menu,
                      self.store_monster_menu,
                      self.store_item_menu,
                      self.multiplayer_menu,
                      self.multiplayer_join_menu,
                      self.multiplayer_join_enter_ip_menu,
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

            if menu.name in ["PLAYER_MONS", "PLAYER_ITEMS"]:
                border_size = menu.border["left-top"].get_width()
                menu.size_x = int(self.resolution[0] * menu.size_ratio[0]) -\
                    (border_size * 2)
                menu.size_y = int(self.resolution[1] * menu.size_ratio[1])
                menu.pos_x = border_size
                menu.pos_y = border_size + ((self.resolution[1]/9)/2)

            elif menu.name in ["STORE_MONS", "STORE_ITEMS"]:
                border_size = menu.border["left-top"].get_width()
                menu.size_x = int(self.resolution[0] * menu.size_ratio[0]) -\
                    (border_size * 2)
                menu.size_y = int(self.resolution[1] * menu.size_ratio[1])
                menu.pos_x = border_size + (self.resolution[0] / 2)
                menu.pos_y = border_size + ((self.resolution[1] / 9) / 2)

            else:
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
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        if self.multiplayer_join_success_menu.interactable:
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                self.game.get_menu_event(self.multiplayer_join_success_menu, event)

        elif self.multiplayer_host_menu.interactable:
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                self.game.get_menu_event(self.multiplayer_host_menu, event)

        elif self.multiplayer_join_menu.interactable:
            self.game.get_menu_event(self.multiplayer_join_menu, event)

        elif self.multiplayer_join_enter_ip_menu.interactable:
            self.game.get_menu_event(self.multiplayer_join_enter_ip_menu, event)

        elif self.multiplayer_menu.interactable:
            self.game.get_menu_event(self.multiplayer_menu, event)

        elif self.item_menu.interactable:
            self.item_menu.get_event(event)

        elif self.monster_menu.interactable:
            self.monster_menu.get_event(event)

        elif self.store_item_menu.interactable:
            self.store_item_menu.get_event(event)

        elif self.store_monster_menu.interactable:
            self.store_monster_menu.get_event(event)

        elif self.pc_menu.interactable:
            self.game.get_menu_event(self.pc_menu, event)

    def draw(self, surface):
        """Draws the start screen to the screen.

        :param surface: Surface to be drawn onto
        :type surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        surface.fill((15, 15, 15))

        self.pc_menu.draw()
        if not networking.networking:
            self.pc_menu.draw_textItem(
                    ["MONSTERS", "ITEMS", "LOG OFF"])
        else:
            self.pc_menu.draw_textItem(
                    ["MONSTERS", "ITEMS", "MULTIPLAYER", "LOG OFF"])

        if self.monster_menu.visible:
            self.monster_menu.draw()
            self.monster_menu.menu_items = []
            self.monster_menu.draw_text("Inventory")
            for monster in self.game.player1.monsters:
                self.monster_menu.menu_items.append(monster.name)
            self.monster_menu.draw_textItem(self.monster_menu.menu_items)

        if self.item_menu.visible:
            self.item_menu.draw()
            self.item_menu.menu_items = []
            self.item_menu.draw_text("Inventory")
            for item in self.game.player1.inventory:
                self.item_menu.menu_items.append(item)
            self.item_menu.draw_textItem(self.item_menu.menu_items)

        if self.store_monster_menu.visible:
            self.store_monster_menu.draw()
            self.store_monster_menu.menu_items = []
            self.store_monster_menu.draw_text("Storage")
            for monster in self.game.player1.storage["monsters"]:
                self.store_monster_menu.menu_items.append(monster.name)
            self.store_monster_menu.draw_textItem(self.store_monster_menu.menu_items)

        if self.store_item_menu.visible:
            self.store_item_menu.draw()
            self.store_item_menu.menu_items = []
            self.store_item_menu.draw_text("Storage")
            for item in self.game.player1.storage["items"]:
                self.store_item_menu.menu_items.append(item)
            self.store_item_menu.draw_textItem(self.store_item_menu.menu_items)

        if self.multiplayer_menu.visible:
            self.multiplayer_menu.draw()
            self.multiplayer_menu.draw_textItem(
                ["HOST A GAME", "SCAN FOR GAMES", "JOIN BY IP"])

        if self.multiplayer_join_menu.visible:
            self.multiplayer_join_menu.draw()
            self.multiplayer_join_menu.draw_text("SELECT GAME:", justify="center")

            # The server list below join by IP
            self.multiplayer_join_menu.draw_textItem(self.game.client.server_list, align="middle", paging=True)

            # If no options are selected because there were no items when
            # the menu was populated, and there are items in the list to
            # select, set the selected item to the top of the list.
            if self.multiplayer_join_menu.selected_menu_item <= 2 and \
            len(self.multiplayer_join_menu.menu_items) > 2:
                self.multiplayer_join_menu.selected_menu_item = 1

        if self.multiplayer_join_enter_ip_menu.visible:
            self.multiplayer_join_enter_ip_menu.draw()

        if self.multiplayer_join_success_menu.visible:
            self.multiplayer_join_success_menu.draw()
            self.multiplayer_join_success_menu.draw_textItem(self.multiplayer_join_success_menu.text)

        if self.multiplayer_host_menu.visible:
            self.multiplayer_host_menu.draw()

            text = "Server Started: \\n"
            for ip in self.multiplayer_host_menu.ips:
                text += ip + "\\n"

            self.multiplayer_host_menu.draw_text(text, justify="center")

