# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.map import RegionProperties
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class AddCollisionAction(EventAction):
    """
    Adds a collision defined by a specific label.
    With numbers, it blocks a specific tile.

    Script usage:
        .. code-block::

            add_collision label

    Script parameters:
        label: Name of the obstacle
        coord: Coordinates map (single coordinate)

    """

    name = "add_collision"
    label: str
    x: Optional[int] = None
    y: Optional[int] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        coords = world.check_collision_zones(world.collision_map, self.label)
        properties = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[],
            key=self.label,
            entity=None,
        )
        if self.x and self.y:
            world.collision_map[(self.x, self.y)] = properties
        if coords:
            for coord in coords:
                world.collision_map[coord] = properties
