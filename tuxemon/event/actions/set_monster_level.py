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
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final, Union


class SetMonsterLevelActionParameters(NamedTuple):
    slot: Union[int, None]
    level: int


@final
class SetMonsterLevelAction(EventAction[SetMonsterLevelActionParameters]):
    """Changes the level of a monster in the current player's party. The action parameters
    may contain a monster slot and the amount by which to level. If no slot is specified,
    all monsters are leveled. The level parameter can be negative, which decreases
    the monster's level.

    Examples:
    set_player_monster 0,5 # Increases the monster in the first slot's level by 5
    set_player_monster ,1  # Increases all player's monsters by 1 level
    set_player_monster 4,-100 # Decreases the monster in the fifth slot's level
                # by 100 levels

    Valid Parameters: slot, level
    """

    name = "set_monster_level"
    param_class = SetMonsterLevelActionParameters

    def start(self) -> None:
        if not self.session.player.monsters:
            return

        monster_slot = self.parameters[0]
        monster_level = self.parameters[1]

        if monster_slot:
            if len(self.session.player.monsters) < int(monster_slot):
                return

            monster = self.session.player.monsters[int(monster_slot)]
            monster.level = max(1, monster.level + int(monster_level))
        else:
            for monster in self.session.player.monsters:
                monster.level = max(1, monster.level + int(monster_level))
