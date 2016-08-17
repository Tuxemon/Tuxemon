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
from functools import partial

from core.components.locale import translator
from core.components.menu.menu import PopUpMenu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug('%s imported' % __name__)


def add_menu_items(state, items):
    for key, callback in items:
        label = translator.translate(key).upper()
        state.build_item(label, callback)


class PCState(PopUpMenu):
    """ The state responsible in game settings.
    """
    shrink_to_items = True

    def startup(self, *items, **kwargs):
        super(PCState, self).startup(*items, **kwargs)

        def change_state(state, **kwargs):
            return partial(self.game.replace_state, state, **kwargs)

        add_menu_items(self, (('menu_monsters', change_state('MonsterMenuState')),
                              ('menu_items', change_state('ItemMenuState')),
                              ('menu_multiplayer', change_state('MultiplayerMenu')),
                              ('log_off', self.game.pop_state)))


class MultiplayerMenu(PopUpMenu):
    """ MP Menu
    """
    shrink_to_items = True

    def startup(self, *items, **kwargs):
        super(MultiplayerMenu, self).startup(*items, **kwargs)

        add_menu_items(self, (('multiplayer_host_game', self.host_game),
                              ('multiplayer_scan_games', self.scan_for_games),
                              ('multiplayer_join_game', self.join_by_ip)))

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
        self.game.push_state("InputState", prompt="Hostname or IP?")
