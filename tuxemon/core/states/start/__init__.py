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
# Leif Theden <leif.theden@gmail.com>
#
#
# core.states.start Handles the start screen which loads and creates new games
#
"""This module contains the Start state.
"""
import logging
from functools import partial

from core import prepare
from core.state import State
from core.components.menu.interface import MenuItem
from core.components.menu.menu import PopUpMenu
from core.components.locale import translator

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class BackgroundState(State):
    """ background state is used to prevent other states from
    being required to track dirty screen areas.  for example,
    in the start state, there is a menu on a blank background,
    since menus do not clean up dirty areas, the blank,
    "Background state" will do that.  The alternative is creating
    a system for states to clean up their dirty screen areas.

    eventually the need for this will be phased out
    """
    def draw(self, surface):
        surface.fill((0, 0, 0, 0))

    def resume(self):
        self.game.pop_state()


class StartState(PopUpMenu):
    """ The state responsible for the start menu.
    """
    shrink_to_items = True

    def startup(self, *args, **kwargs):
        super(StartState, self).startup(*args, **kwargs)

        def change_state(state, **kwargs):
            return partial(self.game.push_state, state, **kwargs)

        def new_game():
            self.game.player1 = prepare.player1
            self.game.replace_state("WorldState")
            self.game.push_state("InputMenu", prompt=translator.translate("input_name"))
            self.game.push_state("FadeInTransition")

        def options():
            pass

        def exit_game():
            self.game.exit = True

        menu_items_map = (
            ('menu_new_game', new_game),
            ('menu_load', change_state("LoadMenuState")),
            ('menu_options', options),
            ('exit', exit_game),
        )

        for key, callback in menu_items_map:
            label = translator.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)
