# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class RemoveCollisionAction(EventAction):
    """
    Removes a collision zone associated with a specific label from the
    world map.

    Script usage:
        .. code-block::

            remove_collision <label>

    Script parameters:
        label: The name or identifier of the obstacle to be removed.
    """

    name = "remove_collision"
    label: str

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        world.remove_collision_label(self.label)
