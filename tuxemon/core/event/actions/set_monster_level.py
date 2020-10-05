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

from tuxemon.core.event.eventaction import EventAction


class SetMonsterLevelAction(EventAction):
    """ Changes the level of a monster in the current player's party. The action parameters
    may contain a monster slot and the amount by which to level. If no slot is specified,
    all monsters are leveled. If no level is specified, the level is reverted to 1.

    Valid Parameters: slot, level
    """
    name = "set_monster_level"
    valid_parameters = [
        (int, "slot"),
        (int, "level")
    ]

    def start(self):
        if not self.session.player.monsters > 0:
            return

        monster_slot = self.parameters[0]
        monster_level = self.parameters[1]

        if monster_slot:
            if len(self.session.player.monsters) < int(monster_slot):
                return

            monster = self.session.player.monsters[int(monster_slot)]
            if monster_level:
                monster.level = max(1, monster.level + int(monster_level))
            else:
                monster.level = 1
        else:
            for monster in self.session.player.monsters:
                if monster_level:
                    monster.level = max(1, monster.level + int(monster_level))
                else:
                    monster.level = 1
