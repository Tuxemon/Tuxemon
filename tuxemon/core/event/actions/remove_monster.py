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


class RemoveMonsterAction(EventAction):
    """Removes a monster to the current player's party if the monster is there.

    Valid Parameters: monster_slug
    """
    name = "remove_monster"
    valid_parameters = [
        (str, "monster_slug")
    ]

    def start(self):
        monster_slug = self.parameters.monster_slug

        # TODO: will give unpredictable result with multiple copies of the same monster
        monster = self.session.player.find_monster(monster_slug)
        if monster:
            self.session.player.remove_monster(monster)
