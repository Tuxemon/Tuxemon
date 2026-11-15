# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

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

    name: ClassVar[str] = "tile_property_updated"
    label: str
    moverate: float

    def test(self, session: Session) -> bool:
        return session.client.terrain_manager.all_tiles_modified(
            self.label, self.moverate
        )
