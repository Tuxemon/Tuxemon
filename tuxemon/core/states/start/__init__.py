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
# Benjamin Bean <superman2k5@gmail.com>
#
#
# core.states.start Handles the start screen which loads and creates new games
#
"""This module contains the Start state.
"""
import logging
from functools import partial

from core import prepare
from core.components.menu.interface import MenuItem
from core.components.menu.menu import PopUpMenu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class StartState(PopUpMenu):
    """ The state responsible for the start menu.
    """
    def initialize_items(self):
        def change_state(state, **kwargs):
            return partial(self.game.push_state, state, **kwargs)

        def new_game():
            self.game.player1 = prepare.player1
            state = self.game.replace_state("WorldState")
            self.game.push_state("FadeInTransition")

        def options():
            pass

        def exit_game():
            self.game.exit = True

        menu_items_map = (
            ('NEW GAME', new_game),
            ('LOAD', change_state("LoadMenuState")),
            ('OPTIONS', options),
            ('EXIT', exit_game),
        )

        for label, callback in menu_items_map:
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, callback)

    def on_menu_selection(self, item):
        item.game_object()

    def calc_final_rect(self):
        rect = self.rect.copy()
        rect.width *= .3
        rect.height *= .5
        rect.center = self.rect.center
        return rect
