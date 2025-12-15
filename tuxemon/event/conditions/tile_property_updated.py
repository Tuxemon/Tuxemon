# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

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

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        label, moverate = condition.parameters
        return session.client.collision_manager.all_tiles_modified(
            label, float(moverate)
        )
