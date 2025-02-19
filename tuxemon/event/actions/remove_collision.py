# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event.eventaction import EventAction
from tuxemon.map import RegionProperties
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class RemoveCollisionAction(EventAction):
    """
    Removes a collision defined by a specific label.

    Script usage:
        .. code-block::

            remove_collision label

    Script parameters:
        label: Name of the obstacle

    """

    name = "remove_collision"
    label: str

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        properties = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            key=self.label,
            entity=None,
        )

        # removes the collision
        coords = world.check_collision_zones(world.collision_map, self.label)
        if coords:
            for coord in coords:
                world.collision_map[coord] = properties
