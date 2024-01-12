# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CharLookAction(EventAction):
    """
    Make a character look around.

    Script usage:
        .. code-block::

            char_look <character>[,frequency][,directions]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        frequency: Frequency of movements. 0 to stop looking. If set to
            a different value it will be clipped to the range [0.5, 5].
            If not passed the default value is 1.
        directions: the direction the character is going to look, by default
            all

        eg. char_look character
        eg. char_look character,,right:left

    """

    name = "char_look"
    character: str
    frequency: Optional[float] = None
    directions: Optional[str] = None

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        world = self.session.client.get_state_by_name(WorldState)
        self.limit_direction: list[Direction] = []
        if self.directions:
            _limit = self.directions.split(":")
            for limit in _limit:
                self.limit_direction.append(Direction(limit))

        def _look(character: NPC) -> None:
            directions = list(Direction)
            # Suspend looking around if a dialog window is open
            for state in self.session.client.active_states:
                if state.name in (
                    "WorldMenuState",
                    "DialogState",
                    "ChoiceState",
                ):
                    return

            # Choose a random direction
            if self.limit_direction:
                directions = self.limit_direction
            direction = random.choice(directions)
            if direction != character.facing:
                character.facing = direction

        def schedule() -> None:
            # The timer is randomized between 0.5 and 1.0 of the frequency
            # parameter
            # Frequency can be set to 0 to indicate that we want to stop
            # looking around
            world.remove_animations_of(schedule)
            if character is None:
                logger.error(f"{self.character} not found")
                return
            elif self.frequency == 0:
                return
            else:
                frequency = 1.0
                if self.frequency:
                    frequency = min(5, max(0.5, self.frequency))
                time = (0.5 + 0.5 * random.random()) * frequency
                world.task(schedule, time)

            _look(character)

        # Schedule the first look
        schedule()
