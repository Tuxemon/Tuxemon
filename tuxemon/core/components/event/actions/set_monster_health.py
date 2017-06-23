# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

from core.components.event.eventaction import EventAction


class SetMonsterHealthAction(EventAction):
    """ Changes the hp of a monster in the current player's party. The action parameters
    may contain a monster slot and the amount of health. If no slot is specified,
    all monsters are healed. If no health is specified, the hp is maxed out.

    Valid Parameters: slot, health
    """
    name = "set_monster_health"
    valid_parameters = [
        (int, "slot"),
        (int, "health")
    ]

    def start(self):
        if not self.game.player1.monsters > 0:
            return

        monster_slot = self.parameters[0]
        monster_health = self.parameters[1]

        if monster_slot:
            if len(self.game.player1.monsters) < int(monster_slot):
                return

            monster = self.game.player1.monsters[int(monster_slot)]
            if monster_health:
                monster.current_hp = int(monster.hp * min(1, max(0, float(monster_health))))
            else:
                monster.current_hp = monster.hp
        else:
            for monster in self.game.player1.monsters:
                if monster_health:
                    monster.current_hp = int(monster.hp * min(1, max(0, float(monster_health))))
                else:
                    monster.current_hp = monster.hp
