# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction
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
    x: Union[int, None] = None
    y: Union[int, None] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        coords = world.check_collision_zones(world.collision_map, self.label)
        if self.x and self.y:
            world.collision_map[(self.x, self.y)] = {
                "enter": [],
                "exit": [],
                "key": self.label,
            }
        else:
            if coords:
                world.collision_map[coords] = {
                    "enter": [],
                    "exit": [],
                    "key": self.label,
                }
