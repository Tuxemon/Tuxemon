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
# core.components.menu.pc_menu
#
"""This module contains the PC Menu
"""
from core.components.menu import Menu
import pygame as pg

class PCMenu(Menu):

    def __init__(self, screen, resolution, game, name="PC Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        if self.menu_items[self.selected_menu_item] == "MONSTERS":

            cs.monster_menu.previous_menu = self
            cs.monster_menu.visible = True
            cs.store_monster_menu.previous_menu = self
            cs.store_monster_menu.visible = True
            cs.pc_menu.interactable = False
            if len(self.game.player1.monsters) == 0:
                cs.monster_menu.interactable = False
                cs.store_monster_menu.interactable = True
                if cs.store_monster_menu.menu_items:
                    cs.store_monster_menu.selected_menu_item = 0
            else:
                cs.monster_menu.interactable = True
                cs.store_monster_menu.interactable = False
                cs.store_monster_menu.selected_menu_item = -1

        elif self.menu_items[self.selected_menu_item] == "ITEMS":
            cs.item_menu.previous_menu = self
            cs.item_menu.visible = True
            cs.store_item_menu.previous_menu = self
            cs.store_item_menu.visible = True
            cs.pc_menu.interactable = False
            if len(self.game.player1.inventory) == 0:
                cs.item_menu.interactable = False
                cs.store_item_menu.interactable = True
                if cs.store_item_menu.menu_items:
                    cs.store_item_menu.selected_menu_item = 0
            else:
                cs.item_menu.interactable = True
                cs.store_item_menu.interactable = False
                cs.store_item_menu.selected_menu_item = -1

        elif self.menu_items[self.selected_menu_item] == "MULTIPLAYER":
            cs.multiplayer_menu.previous_menu = self
            cs.multiplayer_menu.visible = True
            cs.multiplayer_menu.interactable = True
            cs.pc_menu.interactable = False

        elif self.menu_items[self.selected_menu_item] == "LOG OFF":
            self.game.pop_state()


class Player_Menu(Menu):

    def __init__(self, screen, resolution, game, name):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        if event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
           self.visible = False
           self.interactable = False
           for child in self.children:
               child.visible = False
               child.interactable = False

           if self.previous_menu:
                self.previous_menu.interactable = True
                self.previous_menu.visible = True

        if event.type == pg.KEYUP and event.key == pg.K_RIGHT \
                or event.type == pg.KEYUP and event.key == pg.K_LEFT:
            swap_menu(self)

        if event.type == pg.KEYUP and event.key == pg.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 0:
                self.selected_menu_item = len(self.menu_items) - 1

        if event.type == pg.KEYUP and event.key == pg.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > len(self.menu_items) - 1:
                self.selected_menu_item = 0

        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            if not self.menu_items:
                return False
            p1 = self.game.player1
            if self.name == "PLAYER_MONS":
                item = self.selected_menu_item
                p1.storage["monsters"].append(p1.monsters.pop(item))
                if len(p1.monsters) <= 0:
                    swap_menu(self)
                return False

            if self.name == "PLAYER_ITEMS":
                item = self.menu_items[self.selected_menu_item]
                for p_item in p1.inventory:
                    if item == p_item:
                        p1.storage["items"][item] = p1.inventory[p_item]
                        p1.inventory.pop(p_item, None)
                        if len(p1.inventory) <= 0:
                            swap_menu(self)
                        return False


class Storage_Menu(Menu):

    def __init__(self, screen, resolution, game, name):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        if event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
           self.visible = False
           self.interactable = False
           for child in self.children:
               child.visible = False
               child.interactable = False
               child.selected_menu_item = 0
           self.selected_menu_item = -1

           if self.previous_menu:
                self.previous_menu.interactable = True
                self.previous_menu.visible = True

        if event.type == pg.KEYUP and event.key == pg.K_RIGHT \
                or event.type == pg.KEYUP and event.key == pg.K_LEFT:
            swap_menu(self)

        if event.type == pg.KEYUP and event.key == pg.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 0:
                self.selected_menu_item = len(self.menu_items) - 1

        if event.type == pg.KEYUP and event.key == pg.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > len(self.menu_items) - 1:
                self.selected_menu_item = 0

        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            if not self.menu_items:
                return False
            p1 = self.game.player1
            if self.name == "STORE_MONS":
                item = self.selected_menu_item
                if len(p1.monsters) < p1.party_limit:
                    p1.monsters.append(p1.storage["monsters"].pop(item))
                if len(p1.storage["monsters"]) <= 0:
                    swap_menu(self)
                    return False

            if self.name == "STORE_ITEMS":
                item = self.menu_items[self.selected_menu_item]
                for s_item in p1.storage["items"]:
                    if item == s_item:
                        p1.inventory[item] = p1.storage["items"][s_item]
                        p1.storage["items"].pop(s_item, None)
                        if len(p1.storage["items"]) <= 0:
                            swap_menu(self)
                        return False


class Multiplayer_Menu(Menu):

    def __init__(self, screen, resolution, game, name="MULTIPLAYER"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        if self.menu_items[self.selected_menu_item] == "HOST A GAME":
            if not self.game.isclient:
                cs.multiplayer_host_menu.previous_menu = self
                cs.multiplayer_host_menu.visible = True
                cs.multiplayer_host_menu.interactable = True
                cs.multiplayer_menu.interactable = False
                self.game.ishost = True
                self.game.server.server.listen()
                self.game.server.listening = True

                # Enable the client and auto join our own game.
                self.game.client.enable_join_multiplayer = True
                self.game.client.client.listen()
                self.game.client.listening = True

                while not self.game.client.client.registered:
                    self.game.client.client.autodiscover(autoregister=False)
                    if len(self.game.client.client.discovered_servers) > 0:
                        for ip, port in self.game.client.client.discovered_servers:
                            game = (ip, port)
                            self.game.client.client.register(game)

        elif self.menu_items[self.selected_menu_item] == "SCAN FOR GAMES":
            if not self.game.ishost:
                cs.multiplayer_join_menu.previous_menu = self
                cs.multiplayer_join_menu.visible = True
                cs.multiplayer_join_menu.interactable = True
                cs.multiplayer_menu.interactable = False
                self.game.client.enable_join_multiplayer = True
                self.game.client.listening = True
                self.game.client.client.listen()
            else:
                return False

        elif self.menu_items[self.selected_menu_item] == "JOIN BY IP":
            if not self.game.ishost:
                cs.multiplayer_join_enter_ip_menu.previous_menu = self
                cs.multiplayer_join_enter_ip_menu.visible = True
                cs.multiplayer_join_enter_ip_menu.interactable = True
                cs.multiplayer_menu.interactable = False

        else:
            return False



class Multiplayer_Join_Menu(Menu):

    def __init__(self, screen, resolution, game, name="SCAN FOR GAMES"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        try:
            game = self.game.client.available_games[self.selected_menu_item]
            self.game.client.selected_game = game

        except IndexError:
            pass

        if self.game.client.selected_game:
            cs.multiplayer_join_success_menu.previous_menu = self
            cs.multiplayer_join_success_menu.visible = True
            cs.multiplayer_join_success_menu.interactable = True
            cs.multiplayer_join_menu.interactable = False



class Multiplayer_Join_Enter_IP_Menu(Menu):
    """Allows you to enter IP manually.
    """

    def __init__(self, screen, resolution, game, name="JOIN BY IP"):

        # Stuff from the parent menu
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        return False


class Multiplayer_Join_Success_Menu(Menu):

    def __init__(self, screen, resolution, game, name="SUCCESS"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
        self.text = ["Joining. Please wait..."]


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        return False



class Multiplayer_Host_Menu(Menu):

    def __init__(self, screen, resolution, game, name="HOSTING"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay


    def get_event(self, event=None):
        """Run once a menu item has been selected by the core.control.Control
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        cs = self.game.current_state
        return False


def swap_menu(menu):
    for child in menu.children:
        if not child.menu_items:
            return False
        else:
            child.interactable = True
            child.selected_menu_item = 0
            menu.selected_menu_item = -1
            menu.interactable = False
