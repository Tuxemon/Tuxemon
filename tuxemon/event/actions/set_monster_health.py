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

import logging
from typing import NamedTuple, Optional, Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class SetMonsterHealthActionParameters(NamedTuple):
    slot: Union[int, None]
    health: Union[float, None]


@final
class SetMonsterHealthAction(EventAction[SetMonsterHealthActionParameters]):
    """
    Change the hp of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_health [slot][,health]

    Script parameters:
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are healed.
        health: A float value between 0 and 1, which is the percent of max
            hp to be restored to. If no health is specified, the hp is maxed
            out.

    """

    name = "set_monster_health"
    param_class = SetMonsterHealthActionParameters

    @staticmethod
    def set_health(monster: Monster, value: Optional[float]) -> None:
        if value is None:
            monster.current_hp = monster.hp
        else:
            if not 0 <= value <= 1:
                raise ValueError("monster health must between 0 and 1")

            monster.current_hp = int(monster.hp * value)

    def start(self) -> None:
        if not self.session.player.monsters:
            return

        monster_slot = self.parameters[0]
        monster_health = self.parameters[1]

        if monster_slot is None:
            for monster in self.session.player.monsters:
                self.set_health(monster, monster_health)
        else:
            try:
                monster = self.session.player.monsters[monster_slot]
            except IndexError:
                logger.error("invalid monster slot")
            else:
                self.set_health(monster, monster_health)
