# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    Teleports the player to a specified map and coordinates.
    If map_name is 'center', uses the player's faint teleport location.
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

        logger.debug(f"Teleporting to map: {map_name}, x: {x}, y: {y}")
        session.client.event_engine.execute_action(
            "transition_teleport", [map_name, x, y]
        )
        return ItemEffectResult(name=item.name, success=True)
