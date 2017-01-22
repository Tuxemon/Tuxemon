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
# Leif Theden <leif.theden@gmail.com>
#
#
# core.components.states.pc
#
""" This module contains the PCState state.
"""
import logging
from collections import OrderedDict
from functools import partial

from core.tools import open_dialog
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu, PopUpMenu
from core.components.locale import translator

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s imported" % __name__)


class PCState(PopUpMenu):
    """ The state responsible in game settings.
    """
    shrink_to_items = True

    def initialize_items(self):
        def change_state(state, **kwargs):
            return partial(self.game.replace_state, state, **kwargs)

        def multiplayer_menu():
            # self.game.replace_state("MultiplayerMenu")
            open_dialog(self.game, ["Multiplayer not supported."])

        menu_items_map = (
            ('menu_monsters', change_state("MonsterMenuState")),
            ('menu_items', change_state("ItemMenuState")),
            ('menu_multiplayer', multiplayer_menu),
            ('log_off', self.game.pop_state),
        )

        for key, callback in menu_items_map:
            label = translator.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)

# class Player_Menu(Menu):
#
#
#
# class Storage_Menu(Menu):
#
#
#
class MultiplayerMenu(PopUpMenu):
    """ MP Menu, broken

    """
    shrink_to_items = True

    def host_game(self):
        if not self.game.isclient:
            self.game.ishost = True
            self.game.server.server.listen()
            self.game.server.listening = True

            # Enable the client and auto join our own game.
            self.game.client.enable_join_multiplayer = True
            self.game.client.client.listen()
            self.game.client.listening = True

            while not self.game.client.client.registered:
                self.game.client.client.autodiscover(autoregister=False)
                for ip, port in self.game.client.client.discovered_servers:
                    game = (ip, port)
                    self.game.client.client.register(game)

    def scan_for_games(self):
        if not self.game.ishost:
            self.game.client.enable_join_multiplayer = True
            self.game.client.listening = True
            self.game.client.client.listen()

    def join_by_ip(self):
        pass

    def initialize_items(self):
        def make_item(label, callback):
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)

        make_item("HOST GAME", self.host_game)
        make_item("SCAN FOR GAMES", self.scan_for_games)
        make_item("JOIN BY IP", self.join_by_ip)

    def calc_final_rect(self):
        rect = self.rect.copy()
        rect.width *= .35
        rect.height *= .45
        rect.center = self.rect.center
        return rect


class Multiplayer_Join_Menu(Menu):
    pass

#
#
#
# class Multiplayer_Join_Enter_IP_Menu(Menu):
#
#
#
# class Multiplayer_Join_Success_Menu(Menu):
#
#
#
# class Multiplayer_Host_Menu(Menu):
#
