# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import itertools
import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_coords, get_direction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)

MIN_FREQUENCY = 0.5
MAX_FREQUENCY = 5
DEFAULT_FREQUENCY = 1


@final
@dataclass
class CharWanderAction(EventAction):
    """
    Make a character wander around the map.

    Script usage:
        .. code-block::

            char_wander <character>[,frequency][,t_bound][,b_bound]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        frequency: Frequency of movements. 0 to stop wandering. If set to
            a different value it will be clipped to the range [0.5, 5].
            If not passed the default value is 1.
        t_bound: coordinates top_bound vertex (eg 5,7)
        b_bound: coordinates bottom_bound vertex (eg 7,9)

        eg. char_wander character,,5,7,7,9

    """

    name = "char_wander"
    character: str
    frequency: Optional[float] = None
    t_bound_x: Optional[int] = None
    t_bound_y: Optional[int] = None
    b_bound_x: Optional[int] = None
    b_bound_y: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        client = self.session.client
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        world = client.get_state_by_name(WorldState)

        output = self.generate_coordinates()

        def move() -> None:
            # Don't interrupt existing movement
            if character.moving or character.path:
                return

            # character stops if the player looks at it
            tiles = get_coords(player.tile_pos, client.map_size)
            direction = get_direction(player.tile_pos, character.tile_pos)
            if character.tile_pos in tiles and player.facing == direction:
                return

            # Suspend wandering if a dialog window is open
            if any(
                state_name in ("WorldMenuState", "DialogState", "ChoiceState")
                for state_name in self.session.client.active_state_names
            ):
                return

            # Choose a random direction that is free and walk toward it
            origin = (character.tile_pos[0], character.tile_pos[1])
            exits = world.get_exits(origin)
            if exits:
                path = random.choice(exits)
                if not output or path in output:
                    character.path = [path]
                    character.next_waypoint()

        def schedule() -> None:
            """
            Schedules the next wandering action.

            Notes:
                The timer is randomized between 0.5 and 1.0 of the frequency parameter.
                Frequency can be set to 0 to indicate that we want to stop wandering.
            """
            world.remove_animations_of(schedule)
            if self.frequency == 0:
                return
            else:
                frequency = min(
                    MAX_FREQUENCY,
                    max(MIN_FREQUENCY, self.frequency or DEFAULT_FREQUENCY),
                )
                time = (
                    MIN_FREQUENCY + MIN_FREQUENCY * random.random()
                ) * frequency
                world.task(schedule, time)

            move()

        # Schedule the first move
        schedule()

    def generate_coordinates(self) -> list[tuple[int, int]]:
        if not hasattr(self, "_coordinates"):
            top_bound = (
                (self.t_bound_x, self.t_bound_y)
                if self.t_bound_x is not None and self.t_bound_y is not None
                else None
            )
            bottom_bound = (
                (self.b_bound_x, self.b_bound_y)
                if self.b_bound_x is not None and self.b_bound_y is not None
                else None
            )
            if top_bound and bottom_bound:
                x_coords = range(top_bound[0], bottom_bound[0] + 1)
                y_coords = range(top_bound[1], bottom_bound[1] + 1)
                self._coordinates = list(itertools.product(x_coords, y_coords))
            else:
                self._coordinates = []
        return self._coordinates
