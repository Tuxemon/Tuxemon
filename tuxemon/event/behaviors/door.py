# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import (
    Behavior,
    EventObject,
    Operator,
    ParameterizableRule,
    SpatialCondition,
)
from tuxemon.event.eventbehavior import EventBehavior


@dataclass
class DoorBehavior(EventBehavior):
    """
    Expand a `door` behavior into the conditions and actions required
    to transition a character through a doorway or portal.

    This behavior triggers when:
        - The character is standing on the door tile.
        - The character is facing the required direction.

    Once triggered, the character is teleported to the specified
    destination coordinates and oriented to the given direction.

    Script usage:
        .. code-block::

            door <character>,<destination>,<x>,<y>,<direction>

    Script parameters:
        character: The character slug (e.g. "player" or an NPC).
        destination: The map slug to teleport to.
        x: X-coordinate on the destination map.
        y: Y-coordinate on the destination map.
        direction: The direction the character must face to activate
            the door, and the direction they will face after teleporting.

    Examples:
        door player,house_interior,5,3,up
        door npc_guard,town_square,10,12,right
    """

    name = "door"

    def expand(
        self,
        event: EventObject,
        behavior: Behavior,
    ) -> tuple[list[SpatialCondition], list[ParameterizableRule]]:
        character, destination, x, y, direction = behavior.args

        conds = [
            SpatialCondition(
                type="char_at",
                parameters=[character],
                box=event.box,
                operator=Operator.IS,
                name=f"{behavior.name}_at",
            ),
            SpatialCondition(
                type="char_facing",
                parameters=[character, direction],
                box=event.box,
                operator=Operator.IS,
                name=f"{behavior.name}_facing",
            ),
        ]

        acts = [
            ParameterizableRule(
                type="transition_teleport",
                parameters=[character, destination, x, y],
                name=f"{behavior.name}_teleport",
            ),
            ParameterizableRule(
                type="char_face",
                parameters=[character, direction],
                name=f"{behavior.name}_face",
            ),
        ]

        return conds, acts
