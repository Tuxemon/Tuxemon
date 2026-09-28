# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import product
from typing import final

from tuxemon.entity.behavior.base import WanderBehavior
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)

DEFAULT_FREQUENCY = 1


@final
@dataclass
class CharWanderAction(EventAction):
    """
    Assign a WanderBehavior to a character.

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
    frequency: float | None = None
    t_bound_x: int | None = None
    t_bound_y: int | None = None
    b_bound_x: int | None = None
    b_bound_y: int | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        # Compute bounds if provided
        if (
            self.t_bound_x is not None
            and self.t_bound_y is not None
            and self.b_bound_x is not None
            and self.b_bound_y is not None
        ):
            top = (self.t_bound_x, self.t_bound_y)
            bottom = (self.b_bound_x, self.b_bound_y)
            bounds = generate_coordinates(top, bottom)
        else:
            bounds = None

        freq = self.frequency or DEFAULT_FREQUENCY

        # Assign behavior
        character.behavior_policy = WanderBehavior(
            bounds=bounds,
            frequency=freq,
        )


def generate_coordinates(
    top_bound: tuple[int, int],
    bottom_bound: tuple[int, int],
) -> list[tuple[int, int]]:
    """Generates movement boundaries based on top and bottom bounds."""
    x_coords = range(top_bound[0], bottom_bound[0] + 1)
    y_coords = range(top_bound[1], bottom_bound[1] + 1)
    return list(product(x_coords, y_coords))
