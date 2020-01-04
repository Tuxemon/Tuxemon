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
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.components.event.eventaction import EventAction


class SetTeleportFaintAction(EventAction):
    """ Sets the player.faint_map array.

    Valid Parameters: map_name, coordinate_x, coordinate_y

    **Examples:**

    >>> action.__dict__
    {
        "type": "set_teleport_faint",
        "parameters": [
            "healing_center.tmx",
            "7",
            "10"
        ]
    }

    """
    name = "set_teleport_faint"
    valid_parameters = [
        (str, "map_name"),
        (int, "x"),
        (int, "y")
    ]

    def start(self):
        # Get the player object from the self.game.
        player = self.game.player1

        # Set the player variable for the faint location
        player.faint_map[0] = self.parameters.map_name
        player.faint_map[1] = self.parameters.x
        player.faint_map[2] = self.parameters.y
