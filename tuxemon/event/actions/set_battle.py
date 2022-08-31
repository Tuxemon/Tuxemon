#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
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

from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction


class SetBattleActionParameters(NamedTuple):
    battle_list: str


@final
class SetBattleAction(EventAction[SetBattleActionParameters]):
    """
    Set the key in the player.battle_history dictionary.

    Script usage:
        .. code-block::

            set_battle <character>:<result>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").
        result: One among "won", "lost" or "draw"

    """

    name = "set_battle"
    param_class = SetBattleActionParameters

    def start(self) -> None:
        player = self.session.player

        # Split the variable into a key: value pair
        battle_list = self.parameters[0].split(":")
        battle_key = str(battle_list[0])
        battle_value = str(battle_list[1])

        # Append the battle_history dictionary with the key: value pair
        player.battle_history[battle_key] = battle_value
