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

from core import prepare
from core.components.event.eventaction import EventAction


class TeleportAction(EventAction):
    """Teleport the player to a particular map and coordinates

    Valid Parameters: map_name, coordinate_x, coordinate_y

    **Examples:**

    >>> action.__dict__
    {
        "type": "teleport",
        "parameters": [
            "map1.tmx",
            "5",
            "5"
        ]
    }

    """
    name = "teleport"
    valid_parameters = [
        (str, "map_name"),
        (int, "x"),
        (int, "y")
    ]

    def start(self):
        # Get the player object from the self.game.
        player = self.game.player1
        world = self.game.current_state

        # Get the teleport parameters for the position x,y and the map to load.
        map_name = self.parameters.map_name
        position_x = self.parameters.x
        position_y = self.parameters.y

        # If we're doing a screen transition with this teleport, set the map name that we'll
        # load during the apex of the transition.
        # TODO: This only needs to happen once.
        if world.in_transition:
            world.delayed_mapname = map_name

        # Check to see if we're also performing a transition. If we are, wait to perform the
        # teleport at the apex of the transition
        if world.in_transition:
            world.delayed_teleport = True
            # Set the global_x/y variables based on the player's pixel position and the tile size.
            world.delayed_x = player.position[0] - (position_x * player.tile_size[0])
            world.delayed_y = player.position[1] - (position_y * player.tile_size[1]) + player.tile_size[1]
        # If we're not doing a transition, then just do the teleport
        else:
            # Set the global_x/y variables based on the player's pixel position and the tile size.
            world.global_x = player.position[0] - (position_x * player.tile_size[0])
            world.global_y = player.position[1] - (position_y * player.tile_size[1]) + player.tile_size[1]

            map_path = prepare.BASEDIR + "resources/maps/" + map_name
            if map_path != world.current_map.filename:
                world.change_map(map_path)

        # Stop the player's movement so they don't continue their move after they teleported.
        player.moving = False
