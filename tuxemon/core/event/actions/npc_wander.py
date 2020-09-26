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

import math
import random

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventaction import EventAction


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
        npc = get_npc(self.session, self.parameters.npc_slug)
        world = self.session.client.get_state_by_name("WorldState")

        def move():
            # Don't interrupt existing movement
            if npc.moving or npc.path:
                return

            # Suspend wandering if a dialog window is open
            # TODO: this should only be done for the NPC the player is conversing with, not everyone
            for state in self.session.client.active_states:
                if state.name == "DialogState":
                    return

            # Choose a random direction that is free and walk toward it
            origin = (int(npc.tile_pos[0]), int(npc.tile_pos[1]))
            exits = world.get_exits(origin)
            if exits:
                npc.path = [random.choice(exits)]
                npc.next_waypoint()

        def schedule():
            # The timer is randomized between 0.5 and 1.0 of the frequency parameter
            # Frequency can be set to 0 to indicate that we want to stop wandering
            world.remove_animations_of(schedule)
            if npc is None or self.parameters.frequency == 0:
                return
            else:
                frequency = 1
                if self.parameters.frequency:
                    frequency = min(5, max(0.5, self.parameters.frequency))
                time = (0.5 + 0.5 * random.random()) * frequency
                world.task(schedule, time)

            move()

        # Schedule the first move
        schedule()
