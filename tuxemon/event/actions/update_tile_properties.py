# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import SurfaceKeys
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class UpdateTilePropertiesAction(EventAction):
    """
    Update tile properties. Enable movement and/or the moverate.

    Script usage:
        .. code-block::

            update_tile_properties <label>[,moverate]

    Script parameters:
        label: Name of the property
        moverate: Value of the moverate (eg 1 equal moverate)
            moverate 0 = not accessible
            default 1

    eg. "update_tile_properties surfable,0.5"

    """

    name = "update_tile_properties"
    label: str
    moverate: Optional[float] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        coords = world.get_all_tile_properties(world.surface_map, self.label)
        moverate = 1.0 if self.moverate is None else self.moverate
        if coords and self.label in SurfaceKeys:
            prop: dict[str, float] = {}
            prop[self.label] = moverate
            for coord in coords:
                world.surface_map[coord] = prop
