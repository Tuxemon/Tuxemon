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

from typing import NamedTuple, Union, final

from tuxemon.event.eventaction import EventAction


class SetMonsterLevelActionParameters(NamedTuple):
    slot: Union[int, None]
    level: int


@final
class SetMonsterLevelAction(EventAction[SetMonsterLevelActionParameters]):
    """
    Change the level of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_level [slot][,level]

    Script parameters:
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are leveled.
        level: Number of levels to add. Negative numbers are allowed.

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
            monster.set_level(monster.level + int(monster_level))
        else:
            for monster in self.session.player.monsters:
                monster.set_level(monster.level + int(monster_level))
