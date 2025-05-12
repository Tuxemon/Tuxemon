# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class AddCollisionAction(EventAction):
    """
    Handles the addition of a collision zone associated with a specific
    label.
    Optionally, with coordinates provided, it can block a specific tile
    within the map.

    Script usage:
        .. code-block::

            add_collision <label>[,x][,y]

    Script parameters:
        label: The name or identifier of the obstacle.
        x: (Optional) X-coordinate of the specific tile to block.
        y: (Optional) Y-coordinate of the specific tile to block.
    """

    name = "add_collision"
    label: str
    x: Optional[int] = None
    y: Optional[int] = None

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        if self.x and self.y:
            world.add_collision_position(self.label, (self.x, self.y))
        else:
            world.add_collision_label(self.label)
