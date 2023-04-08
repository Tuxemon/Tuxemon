# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class RemoveCollisionAction(EventAction):
    """
    Adds a collision.

    Script usage:
        .. code-block::

            remove_collision label

    Script parameters:
        label: Name of the obstacle (water, etc.)

    """

    name = "remove_collision"
    label: str

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        # removes the collision
        coords = world.check_collision_zones(world.collision_map, self.label)
        if coords:
            del world.collision_map[coords]
