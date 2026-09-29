# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.map.region import RegionProperties
from tuxemon.session import Session


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
    x: int | None = None
    y: int | None = None

    def start(self, session: Session) -> None:
        client = session.client.collision_manager
        region = RegionProperties().with_overrides(key=self.label)

        if self.x is not None and self.y is not None:
            client._map_manager.collision_map[(self.x, self.y)] = region
        else:
            coords = client.check_collision_zones(
                client._map_manager.collision_map, self.label
            )
            for coord in coords:
                client._map_manager.collision_map[coord] = region
