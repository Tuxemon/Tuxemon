# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)

DEFAULT_FREQUENCY = 1


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

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        world = session.client.get_state_by_name(WorldState)

        if not character:
            logger.error(f"{self.character} not found")
            return

        self.limit_direction: list[Direction] = []
        if self.directions:
            self.limit_direction = [
                Direction(limit) for limit in self.directions.split(":")
            ]

        def _look() -> None:
            # Suspend looking around if a dialog window is open
            if any(
                state_name in ("WorldMenuState", "DialogState", "ChoiceState")
                for state_name in session.client.active_state_names
            ):
                return

            # Choose a random direction
            directions = self.limit_direction or list(Direction)
            direction = random.choice(directions)
            if direction != character.facing:
                character.set_facing(direction)

        # Schedule the first look
        frequency = self.frequency or DEFAULT_FREQUENCY
        world.schedule_callback(frequency, _look)
