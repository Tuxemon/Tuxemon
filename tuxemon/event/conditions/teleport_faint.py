# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class TeleportFaintCondition(EventCondition):
    """
    Check to see if teleport_faint exists and has a particular value.

    If the teleport_faint does not exist it will return ``False``.

    Script usage:
        .. code-block::

            is teleport_faint character,[map_name],[x],[y]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        map_name: The name of the map to validate against.
        x: The x-coordinate to validate against.
        y: The y-coordinate to validate against.
    """

    name = "teleport_faint"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character = condition.parameters[0]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        if len(condition.parameters) == 1:
            return character.teleport_faint.is_default()
        elif len(condition.parameters) > 1:
            _map_name = condition.parameters[1]
            _x = condition.parameters[2]
            _y = condition.parameters[3]
            return character.teleport_faint.is_valid(
                map_name=_map_name, x=int(_x), y=int(_y)
            )
        else:
            return False
