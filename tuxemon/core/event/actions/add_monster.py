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

from tuxemon.core import monster
from tuxemon.core.event.eventaction import EventAction


class AddMonsterAction(EventAction):
    """Adds a monster to the current player's party if there is room.

    The action parameter must contain a monster slug to look up in the monster database.

    Valid Parameters: monster_slug, level
    """
    name = "add_monster"
    valid_parameters = [
        (str, "monster_slug"),
        (int, "monster_level")
    ]

    def start(self):
        monster_slug, monster_level = self.parameters

        current_monster = monster.Monster()
        current_monster.load_from_db(monster_slug)
        current_monster.set_level(monster_level)
        current_monster.current_hp = current_monster.hp

        self.session.player.add_monster(current_monster)
