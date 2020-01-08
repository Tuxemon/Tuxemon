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


class NpcWanderAction(EventAction):
    """ Makes an NPC wander around the map

    Valid Parameters: npc_slug, frequency
    """
    name = "npc_wander"
    valid_parameters = [
        (str, "npc_slug"),
        (float, "frequency")
    ]

    def start(self):
        npc = get_npc(self.game, self.parameters.npc_slug)
        world = self.game.get_state_name("WorldState")
        collisions = world.get_collision_map()

        def move():
            # Don't interrupt existing movement
            if npc.moving or npc.path:
                return

            # Suspend wandering if a dialog window is open
            # TODO: this should only be done for the NPC the player is conversing with, not everyone
            for state in self.game.active_states:
                if state.name == "DialogState":
                    return

            # Choose a random direction
            direction = random.choice(["up", "down", "left", "right"])
            origin = (int(npc.tile_pos[0] + dirs2[direction][0]), int(npc.tile_pos[1] + dirs2[direction][1]))

            # Check if either a collision, the player or another NPC are blocking the way
            blocked = origin in collisions
            for ent in world.npcs.values():
                if origin[0] == int(ent.tile_pos[0]) and origin[1] == int(ent.tile_pos[1]):
                    blocked = True

            # Go to the chosen position if the tile is free, look toward it if not
            if blocked:
                npc.facing = direction
            else:
                npc.move_one_tile(direction)

        def schedule():
            # Check that the NPC still exists
            if npc is None:
                return

            move()

            # The timer is randomized between 0.5 and 1.0 of the frequency parameter
            frequency = 1
            if self.parameters.frequency:
                frequency = min(5, max(0.5, self.parameters.frequency))
            time = (0.5 + 0.5 * random.random()) * frequency
            world.task(schedule, time)

        # Schedule the first move
        schedule()
