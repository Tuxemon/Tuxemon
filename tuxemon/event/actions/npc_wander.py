# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class NpcWanderAction(EventAction):
    """
    Make an NPC wander around the map.

    Script usage:
        .. code-block::

            npc_wander <npc_slug> [frequency]

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        frequency: Frequency of movements. 0 to stop wandering. If set to
            a different value it will be clipped to the range [0.5, 5].
            If not passed the default value is 1.

    """

    name = "npc_wander"
    npc_slug: str
    frequency: Union[float, None] = None

    def start(self) -> None:
        player = self.session.player
        npc = get_npc(self.session, self.npc_slug)
        world = self.session.client.get_state_by_name(WorldState)

        def move(world: WorldState, npc: NPC) -> None:
            # Don't interrupt existing movement
            if npc.moving or npc.path:
                return

            # Suspend wandering if a dialog window is open
            coords = (0, 0)
            for state in self.session.client.active_states:
                if state.name == "DialogState":
                    # retrieve NPC talking to
                    if player.facing == "down":
                        coords = (player.tile_pos[0], player.tile_pos[1] + 1)
                    elif player.facing == "up":
                        coords = (player.tile_pos[0], player.tile_pos[1] - 1)
                    elif player.facing == "left":
                        coords = (player.tile_pos[0] - 1, player.tile_pos[1])
                    elif player.facing == "right":
                        coords = (player.tile_pos[0] + 1, player.tile_pos[1])
                elif state.name == "WorldMenuState":
                    return

            # Choose a random direction that is free and walk toward it
            origin = (int(npc.tile_pos[0]), int(npc.tile_pos[1]))
            exits = world.get_exits(origin)
            if exits:
                if origin != coords:
                    npc.path = [random.choice(exits)]
                    npc.next_waypoint()
                else:
                    return

        def schedule() -> None:
            # The timer is randomized between 0.5 and 1.0 of the frequency
            # parameter
            # Frequency can be set to 0 to indicate that we want to stop
            # wandering
            world.remove_animations_of(schedule)
            if npc is None or self.frequency == 0:
                return
            else:
                frequency = 1.0
                if self.frequency:
                    frequency = min(5, max(0.5, self.frequency))
                time = (0.5 + 0.5 * random.random()) * frequency
                world.task(schedule, time)

            move(world, npc)

        # Schedule the first move
        schedule()
