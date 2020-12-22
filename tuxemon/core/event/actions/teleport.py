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

from tuxemon.core.euclid import Vector3
from tuxemon.core.event.eventaction import EventAction


class TeleportAction(EventAction):
    """Teleport the player to a particular map and tile coordinates

    Valid Parameters: map_name, coordinate_x, coordinate_y

    **Examples:**

    >>> action.__dict__
    {
        "type": "teleport",
        "parameters": [
            "taba_town.tmx",
            "5",
            "5"
        ]
    }

    """

    name = "teleport"
    valid_parameters = [(str, "map_name"), (int, "x"), (int, "y")]

    def start(self):
        position = Vector3(self.parameters.x, self.parameters.y, 0)
        self.context.client.release_controls()
        self.context.world.teleport(self.context.player, self.parameters.map_name, position)
