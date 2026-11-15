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
class CheckTeleportFaintCondition(EventCondition):
    """
    Check to see if check_teleport_faint exists and has a particular value.

    If the teleport_faint does not exist it will return ``False``.

    Script usage:
        .. code-block::

            is check_teleport_faint character,[map_name],[x],[y]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        map_name: The name of the map to validate against.
        x: The x-coordinate to validate against.
        y: The y-coordinate to validate against.
    """

    name: ClassVar[str] = "check_teleport_faint"
    character: str
    map_name: str | None = None
    x_coord: int | None = None
    y_coord: int | None = None

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        if self.map_name and self.x_coord and self.y_coord:
            return character.teleport_faint.is_valid(
                map_name=self.map_name, x=self.x_coord, y=self.y_coord
            )
        else:
            return character.teleport_faint.is_default()
