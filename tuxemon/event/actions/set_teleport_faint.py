# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.teleporter import TeleportFaint

logger = logging.getLogger(__name__)


@final
@dataclass
class SetTeleportFaintAction(EventAction):
    """
    Set teleport faint data

    Script usage:
        .. code-block::

            set_teleport_faint <character>,<map_name>,<x>,<y>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        map_name: The name of the map to validate against.
        x: The x-coordinate to validate against.
        y: The y-coordinate to validate against.
    """

    name = "set_teleport_faint"
    character: str
    map_name: str
    x: int
    y: int

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        character.teleport_faint = TeleportFaint(self.map_name, self.x, self.y)
