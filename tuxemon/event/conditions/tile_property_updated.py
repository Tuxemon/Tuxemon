# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@dataclass
class TilePropertyUpdatedCondition(EventCondition):
    """
    Checks whether all relevant tiles in the world have been
    modified with a specific property.

    Script usage:
        .. code-block::

            is tile_property_updated <label>,<moverate>

    Script parameters:
        label: The property name to check (e.g., terrain type).
        moverate: The expected movement rate value.
    """

    name = "tile_property_updated"

    def test(self, session: Session, condition: MapCondition) -> bool:
        label, moverate = condition.parameters
        world = session.client.get_state_by_name(WorldState)
        return world.all_tiles_modified(label, float(moverate))
