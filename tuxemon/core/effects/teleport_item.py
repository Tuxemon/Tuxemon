# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class TeleportItemEffect(CoreEffect):
    """
    Applies the "teleport_item" effect to an item.

    This effect teleports the player to a specified map and coordinates.
    It can either use explicit coordinates provided in the item definition
    or, if ``map_name`` is set to ``center``, teleport the player to their
    faint recovery location.

    **Parameters**

    - ``map_name``: The destination map name.
      - If ``center`` → uses the player's faint teleport location.
      - Otherwise → uses the specified map name.
    - ``coord_x``: Integer X-coordinate for teleport destination (default: -1).
    - ``coord_y``: Integer Y-coordinate for teleport destination (default: -1).

    **Example**

    .. code-block:: json

        "effects": [
            "teleport_item town_square 10 5"
        ]

        "effects": [
            "teleport_item center"
        ]
    """

    name = "teleport_item"
    map_name: str
    coord_x: int = -1
    coord_y: int = -1

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        character = session.player

        if self.map_name == "center":
            map_name = character.teleport_faint.map_name
            x = character.teleport_faint.x
            y = character.teleport_faint.y
        else:
            map_name = self.map_name
            x = self.coord_x
            y = self.coord_y

        logger.debug(
            f"Teleporting to map: {character.name} to {map_name}, x: {x}, y: {y}"
        )
        session.client.event_engine.execute_action(
            "transition_teleport", ["player", map_name, x, y]
        )
        return ItemEffectResult(name=item.name, success=True)
