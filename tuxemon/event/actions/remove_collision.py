# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event.eventaction import EventAction
from tuxemon.map.region import RegionProperties
from tuxemon.session import Session


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
        region = RegionProperties().with_overrides(
            enter_from=list(Direction),
            exit_from=list(Direction),
            key=self.label,
        )
        coords = session.client.collision_manager.check_collision_zones(
            session.client.map_manager.collision_map, self.label
        )
        for coord in coords:
            session.client.map_manager.collision_map[coord] = region
