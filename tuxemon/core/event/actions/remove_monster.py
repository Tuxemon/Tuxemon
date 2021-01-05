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
import uuid

from tuxemon.core.event.eventaction import EventAction


class RemoveMonsterAction(EventAction):
    """Removes a monster from the current player's party if the monster is there.

    Valid Parameters: instance_id
    """
    name = "remove_monster"
    valid_parameters = [
        (str, "instance_id")
    ]

    def start(self):
        iid = self.session.player.game_variables[self.parameters.instance_id]
        instance_id = uuid.UUID(iid)

        monster = self.session.player.find_monster_by_id(instance_id)
        if monster is not None:
            self.session.player.remove_monster(monster)
