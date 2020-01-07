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

import math
import random

from tuxemon.core.components.event import get_npc
from tuxemon.core.components.event.eventaction import EventAction
from tuxemon.core.components.map import dirs2


# Picks a random position from the cubic area around the origin
def pick_target(origin, tiles, collisions):
    origins = []
    for x in range(origin[0] - tiles, origin[0] + tiles):
        for y in range(origin[1] - tiles, origin[1] + tiles):
            org = (x, y)
            if (org) not in collisions:
                origins.append(org)
    return random.choice(origins)


class NpcWanderAction(EventAction):
    """ Makes an NPC wander around the map

    Valid Parameters: npc_slug, frequency, tiles
    """
    name = "npc_wander"
    valid_parameters = [
        (str, "npc_slug"),
        (float, "frequency"),
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

            # Choose a random distance
            tiles_max = 4
            if self.parameters.tiles:
                tiles_max = self.parameters.tiles
            tiles = int(max(1, math.ceil(tiles_max * random.random())))

            # Pick a new location to move to
            origin = (int(npc.tile_pos[0]), int(npc.tile_pos[1]))
            target = pick_target(origin, tiles, collisions)
            npc.pathfind(target)

        def next():
            # Check that the NPC still exists
            if npc is None:
                return

            move()

            # Randomly repeat between time / 2 and time
            time_max = 2
            if self.parameters.frequency:
                time_max = self.parameters.frequency
            time = (time_max / 2) + ((time_max / 2) * random.random())
            world.task(next, min(10, max(0.5, time)))

        # Initialize the schedule function
        next()
