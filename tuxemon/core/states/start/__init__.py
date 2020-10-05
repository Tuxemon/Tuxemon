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

from tuxemon.core import prepare
from tuxemon.core.locale import T
from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import PopUpMenu
from tuxemon.core.save import get_index_of_latest_save
from tuxemon.core.session import local_session
from tuxemon.core.state import State

logger = logging.getLogger(__name__)


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


class StartState(PopUpMenu):
    """ The state responsible for the start menu.
    """
    escape_key_exits = False
    shrink_to_items = True

    def startup(self, *args, **kwargs):
        # If there is a save, then move the cursor to "Load game" first
        index = get_index_of_latest_save()
        kwargs['selected_index'] = 0 if index is None else 1
        super().startup(*args, **kwargs)

        def change_state(state, **change_state_kwargs):
            return partial(self.client.push_state, state, **change_state_kwargs)

        def set_player_name(text):
            local_session.player.name = text

        def new_game():
            # load the starting map
            state = self.client.replace_state("WorldState")
            map_name = prepare.fetch("maps", prepare.CONFIG.starting_map)
            state.change_map(map_name)
            self.client.push_state(
                state_name="InputMenu",
                prompt=T.translate("input_name"),
                callback=set_player_name,
                escape_key_exits=False,
            )
            self.client.push_state("FadeInTransition")

        def options():
            pass

        def exit_game():
            self.client.exit = True

        menu_items_map = (
            ('menu_new_game', new_game),
            ('menu_load', change_state("LoadMenuState")),
            ('menu_options', options),
            ('exit', exit_game),
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)
