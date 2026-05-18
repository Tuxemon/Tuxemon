# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.entity.path.commands import (
    ContinueCommand,
    MovementCommand,
    PushCommand,
    SpeedCommand,
)

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.entity.path.path_view import PathView
    from tuxemon.map.region import RegionProperties


logger = logging.getLogger(__name__)


class TileEffectProcessor:
    """
    Handles tile-based effects such as push tiles, speed modifiers,
    and (optionally) continue tiles, by returning movement commands.
    """

    def get_effects(
        self,
        tile: RegionProperties | None,
        owner: NPC,
        path: PathView,
    ) -> list[MovementCommand]:
        """
        Interpret tile properties into movement commands.
        """
        commands: list[MovementCommand] = []
        if tile is None:
            return commands

        # Push tiles
        if tile.push_effect:
            commands.append(
                PushCommand(
                    direction=tile.push_effect.direction,
                    strength=tile.push_effect.strength,
                )
            )

        # Speed modifiers
        if tile.speed_modifier:
            commands.append(SpeedCommand(tile.speed_modifier))

        # Continue tiles
        if tile.endure:
            if len(tile.endure) > 1:
                direction = owner.facing
            else:
                direction = tile.endure[0]
            commands.append(ContinueCommand(direction))

        return commands
