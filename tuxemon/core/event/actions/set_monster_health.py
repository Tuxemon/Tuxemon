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

import logging

from tuxemon.core.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class SetMonsterHealthAction(EventAction):
    """ Changes the hp of a monster in the current player's party. The action parameters
    may contain a monster slot and the amount of health. If no slot is specified,
    all monsters are healed. If no health is specified, the hp is maxed out.

    health is a float value between 0 and 1, which is the percent of max hp to be restored to

    Valid Parameters: slot, health
    """
    name = "set_monster_health"
    valid_parameters = [
        (int, "slot"),
        (float, "health")
    ]

    @staticmethod
    def set_health(monster, value):
        if value is None:
            monster.current_hp = monster.hp
        else:
            if not 0 <= value <= 1:
                logger.error("monster health must between 0 and 1")
                raise ValueError

            monster.current_hp = int(monster.hp * value)

    def start(self):
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
