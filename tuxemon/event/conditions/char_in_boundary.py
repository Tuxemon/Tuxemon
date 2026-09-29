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
class CharInBoundaryCondition(EventCondition):
    """
    Checks if a character is within a specific named boundary.

    Script usage:
        .. code-block::

            is char_in_boundary <character_name>,<boundary_name>

    Script parameters:
        character_name: "player" or an NPC slug.
        boundary_name: The name of the boundary to check (e.g., "safe_zone").
    """

    name: ClassVar[str] = "char_in_boundary"
    character_name: str
    boundary_name: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character_name)
        if character is None:
            logger.error(f"Character '{self.character_name}' not found.")
            return False

        checker = session.client.boundary
        try:
            boundary = checker.boundaries[self.boundary_name]
        except KeyError:
            logger.error(f"Boundary '{self.boundary_name}' not found.")
            return False

        return boundary.is_within(character.tile_pos)
