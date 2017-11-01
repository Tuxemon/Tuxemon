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


class DelayedTeleportAction(EventAction):
    """ Set teleport information.  Teleport will be triggered during screen transition

    Only use this if followed by a transition
    """
    name = "delayed_teleport"
    valid_parameters = [
        (str, "map_name"),
        (int, "position_x"),
        (int, "position_y")
    ]

    def start(self):
        # Get the world object from the self.game.
        world = self.game.get_state_name("WorldState")

        # give up if there is a teleport in progress
        if world.delayed_teleport:
            return

        # Get the teleport parameters for the position x,y and the map to load.
        mapname, position_x, position_y = self.parameters

        world.delayed_mapname = mapname
        world.delayed_teleport = True

        # Get the player object from the self.game.
        player = self.game.player1

        # Set the global_x/y variables based on the player's pixel position and the tile size.
        world.delayed_x = player.position[0] - (position_x * player.tile_size[0])
        world.delayed_y = player.position[1] - (position_y * player.tile_size[1]) + player.tile_size[1]
