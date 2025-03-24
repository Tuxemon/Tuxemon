# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.db import Direction

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


class Teleporter:
    """
    Manages teleportation of characters in the game world.

    This class provides methods for teleporting characters to specific locations,
    as well as handling delayed teleportations that occur during screen transitions.

    Attributes:
        delayed_teleport: Whether a delayed teleportation is pending.
        delayed_char: The character to teleport, or None if the player.
        delayed_mapname: The name of the map to teleport to.
        delayed_x: The X position to teleport to.
        delayed_y: The Y position to teleport to.
        delayed_facing: The direction to face after teleporting.

    """

    def __init__(self, world: WorldState) -> None:
        self.world = world
        self.delayed_teleport = False
        self.delayed_char: Optional[NPC] = None
        self.delayed_mapname = ""
        self.delayed_x = 0
        self.delayed_y = 0
        self.delayed_facing: Optional[Direction] = None

    def handle_delayed_teleport(self, character: NPC) -> None:
        """
        Handle a delayed teleportation during a screen transition.

        Parameters:
            world: The current game state.
            char: The character to teleport, or None if the player.

        """
        if self.delayed_teleport:
            self.teleport_character(
                self.delayed_char or character,
                self.delayed_mapname,
                self.delayed_x,
                self.delayed_y,
            )
            if self.delayed_facing:
                (self.delayed_char or character).facing = self.delayed_facing
                self.delayed_facing = None
            self.delayed_teleport = False

    def teleport_character(
        self,
        character: NPC,
        map_name: str,
        x: int,
        y: int,
    ) -> None:
        """
        Teleport a character to a specific map and tile coordinates.

        Parameters:
            world: The current game state.
            char: The character to teleport.
            map_name: The name of the map to teleport to.
            x: The X coordinate of the map to teleport to.
            y: The Y coordinate of the map to teleport to.

        Raises:
            ValueError: If the character is outside the boundaries of the new map.
        """
        self.world.stop_char(character)
        self.world.lock_controls(character)

        target_map = prepare.fetch("maps", map_name)

        logger.debug(f"Removing {character.slug}'s collision zone")
        character.remove_collision()

        if (
            self.world.current_map is None
            or target_map != self.world.current_map.filename
        ):
            self.world.change_map(target_map)
            logger.debug(f"Loaded map '{target_map}'")

            if not self.world.boundary_checker.is_within_boundaries((x, y)):
                raise ValueError(
                    f"Character is outside the boundaries of the map at ({x}, {y})"
                )

        logger.debug(f"Stopping {character.slug}'s movements")
        character.cancel_path()

        logger.debug(f"Setting {character.slug}'s position to ({x}, {y})")
        character.set_position((x, y))

        logger.debug(f"Unlocking {character.slug}'s controls")
        self.world.unlock_controls(character)
