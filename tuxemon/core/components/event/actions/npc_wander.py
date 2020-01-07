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

import random

from tuxemon.core.components.event import get_npc
from tuxemon.core.components.event.eventaction import EventAction
from tuxemon.core.components.map import dirs2


def single_dir(origin, direction, tiles, collisions):
    origin = tuple(origin) # make copy to prevent modifying the npc
    for i in range(tiles):
        origin_ofs = dirs2[direction]
        if tuple(origin + origin_ofs) in collisions:
            break
        origin += origin_ofs
    return origin


class NpcWanderAction(EventAction):
    """ Makes an NPC wander

    Valid Parameters: npc_slug, time, distance
    """
    name = "npc_wander"
    valid_parameters = [
        (str, "npc_slug"),
        (float, "time"),
        (int, "tiles")
    ]

    def start(self):
        npc = get_npc(self.game, self.parameters.npc_slug)
        world = self.game.get_state_name("WorldState")
        collisions = world.get_collision_map()

        def move():
            # Don't interrupt existing movement
            if npc.moving or npc.path:
                return

            # Choose a direction
            direction_random = random.random()
            direction = "up"
            if direction_random > 0.75:
                direction = "down"
            elif direction_random > 0.5:
                direction = "left"
            elif direction_random > 0.25:
                direction = "right"

            # Choose a distance
            tiles_max = 4
            if self.parameters.tiles:
                tiles_max = self.parameters.tiles
            tiles = int(round(tiles_max * random.random(), 0))

            # Move is there's at least one tile, change direction otherwise
            if tiles > 0:
                parameters = [direction + " " + str(tiles)]
                npc.pathfind((single_dir(npc.tile_pos, direction, tiles, collisions)))
            else:
                npc.facing = direction

        def next():
            # Check that the NPC still exists
            if npc is None:
                return

            # Issue the move command
            move()

            # Run this function again between time / 2 and time
            time_max = 2
            if self.parameters.time:
                time_max = self.parameters.time
            time = min(10, max(0.1, (time_max / 2) + ((time_max / 2) * random.random())))

            # Schedule the next move
            world.task(next, time)

        # Initialize the schedule function
        next()
