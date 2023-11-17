# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, cast, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import Direction
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class NpcLookAction(EventAction):
    """
    Make an NPC look around.

    Script usage:
        .. code-block::

            npc_look <npc_slug>[,frequency][,directions]

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        frequency: Frequency of movements. 0 to stop looking. If set to
            a different value it will be clipped to the range [0.5, 5].
            If not passed the default value is 1.
        directions: the direction the npc is going to look, by default
            all

        eg. npc_look npc_slug
        eg. npc_look npc_slug,,right:left

    """

    name = "npc_look"
    npc_slug: str
    frequency: Optional[float] = None
    directions: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        npc = get_npc(self.session, self.npc_slug)
        world = self.session.client.get_state_by_name(WorldState)
        self.limit_direction = []
        if self.directions:
            self.limit_direction = self.directions.split(":")

        def _look(npc: NPC) -> None:
            directions: list[str] = ["up", "down", "right", "left"]
            # Suspend looking around if a dialog window is open
            for state in self.session.client.active_states:
                if state.name == "DialogState":
                    # retrieve NPC talking to
                    if player.facing in directions:
                        return
                elif state.name == "WorldMenuState":
                    return

            # Choose a random direction
            if self.limit_direction:
                directions = self.limit_direction
            direction = random.choice(directions)
            if direction != npc.facing:
                npc.facing = cast(Direction, direction)

        def schedule() -> None:
            # The timer is randomized between 0.5 and 1.0 of the frequency
            # parameter
            # Frequency can be set to 0 to indicate that we want to stop
            # looking around
            world.remove_animations_of(schedule)
            if npc is None or self.frequency == 0:
                return
            else:
                frequency = 1.0
                if self.frequency:
                    frequency = min(5, max(0.5, self.frequency))
                time = (0.5 + 0.5 * random.random()) * frequency
                world.task(schedule, time)

            _look(npc)

        # Schedule the first look
        schedule()
