# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
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

    name = "char_in_boundary"
    character_name: str
    boundary_name: str

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        character_name, boundary_name = condition.parameters
        character = get_npc(session, character_name)
        if character is None:
            logger.error(f"Character '{character_name}' not found.")
            return False

        checker = session.client.boundary
        try:
            boundary = checker.boundaries[boundary_name]
        except KeyError:
            logger.error(f"Boundary '{boundary_name}' not found.")
            return False

        return boundary.is_within(character.tile_pos)
