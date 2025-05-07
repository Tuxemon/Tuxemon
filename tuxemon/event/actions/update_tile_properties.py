# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class UpdateTilePropertiesAction(EventAction):
    """
    Update tile properties by modifying movement settings or accessibility.

    Script usage:
        .. code-block::

            update_tile_properties <label>[,moverate]

    Script parameters:
        label: The name of the property to update (e.g., surfable, walkable).
        moverate: The value of the movement rate (e.g., 1 for normal movement,
            0 for inaccessible).

    Example:
        "update_tile_properties surfable,0.5" sets the surfable property to 0.5
        for relevant tiles.
    """

    name = "update_tile_properties"
    label: str
    moverate: float

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        world.update_tile_property(self.label, self.moverate)
