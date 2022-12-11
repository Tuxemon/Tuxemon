#
# Tuxemon
# Copyright (c) 2020      William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>

from __future__ import annotations

import logging
from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState

logger = logging.getLogger(__name__)


class GetPlayerMonsterActionParameters(NamedTuple):
    variable_name: str


# noinspection PyAttributeOutsideInit
@final
class GetPlayerMonsterAction(EventAction[GetPlayerMonsterActionParameters]):
    """
    Select a monster in the player party and store its id in a variable.

    Script usage:
        .. code-block::

            get_player_monster <variable_name>

    Script parameters:
        variable_name: Name of the variable where to store the monster id.

    """

    name = "get_player_monster"
    param_class = GetPlayerMonsterActionParameters

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        self.player.game_variables[
            self.variable
        ] = menu_item.game_object.instance_id.hex
        self.session.client.pop_state()

    def start(self) -> None:
        self.player = self.session.player
        self.variable = self.parameters.variable_name

        # pull up the monster menu so we know which one we are saving
        menu = self.session.client.push_state(MonsterMenuState)
        menu.on_menu_selection = self.set_var  # type: ignore[assignment]

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
