# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.db import Direction

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@dataclass
class TeleportFaint:
    map_name: str = "default.tmx"
    x: int = 0
    y: int = 0

    @classmethod
    def from_tuple(cls, data: tuple[str, int, int]) -> TeleportFaint:
        return cls(data[0], data[1], data[2])

    def is_valid(self, map_name: str, x: int, y: int) -> bool:
        return self.map_name == map_name and self.x == x and self.y == y

    def is_default(self) -> bool:
        return self.map_name == "default.tmx" and self.x == 0 and self.y == 0

    def to_tuple(self) -> tuple[str, int, int]:
        return (self.map_name, self.x, self.y)

    def to_list(self) -> list[str]:
        return [self.map_name, str(self.x), str(self.y)]


class Teleporter:
    """
    Manages teleportation of characters in the game world.

    This class provides methods for teleporting characters to specific
    locations, as well as handling delayed teleportations that occur
    during screen transitions.

    Attributes:
        delayed_teleport: Whether a delayed teleportation is pending.
        delayed_char: The character to teleport, or None if the player.
        delayed_mapname: The name of the map to teleport to.
            Must exist in the world state.
        delayed_x: The X position to teleport to.
            Must be valid within the map boundaries.
        delayed_y: The Y position to teleport to.
            Must be valid within the map boundaries.
        delayed_facing: The direction to face after teleporting.
            Should align with the world context.
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
        if self.delayed_teleport:
            self.execute_delayed_teleport(character)

    def execute_delayed_teleport(self, character: NPC) -> None:
        """
        Executes the delayed teleportation.

        Parameters:
            char: The character to teleport, or None if the player.
        """
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
            character: The character object to teleport.
            map_name: The name of the map to teleport to.
            x: The X coordinate of the target map.
            y: The Y coordinate of the target map.

        Raises:
            ValueError: If the character is outside the boundaries of
            the new map.
        """
        self.prepare_teleport(character)
        self._switch_map_if_needed(map_name)
        self._update_character_position(character, x, y)
        self.finalize_teleport(character)

    def prepare_teleport(self, character: NPC) -> None:
        """
        Prepare the character for teleportation by stopping movement and
        locking controls.

        Parameters:
            character: The character to prepare for teleportation.
        """
        logger.debug(f"Preparing {character.slug} for teleportation...")
        self.world.stop_char(character)

        if len(self.world.client.state_manager.active_states) == 2:
            self.world.client.push_state_with_timeout("TeleporterState", 15)

        self.world.lock_controls(character)
        logger.info(f"{character.slug} is prepared for teleportation.")

    def finalize_teleport(self, character: NPC) -> None:
        """
        Finalize the teleportation process by unlocking controls and resetting
        the character's state.

        Parameters:
            character: The character to finalize teleportation for.
        """
        logger.debug(f"Finalizing teleportation for {character.slug}...")
        self.world.unlock_controls(character)
        logger.info(f"{character.slug} has completed teleportation.")

    def _switch_map_if_needed(self, map_name: str) -> None:
        if (
            self.world.current_map is None
            or map_name != self.world.current_map.filename
        ):
            target_map = prepare.fetch("maps", map_name)
            if not target_map:
                raise ValueError(f"Map '{map_name}' does not exist.")
            self.world.change_map(target_map)

    def _update_character_position(
        self, character: NPC, x: int, y: int
    ) -> None:
        if not self.world.boundary_checker.is_within_boundaries((x, y)):
            raise ValueError(
                f"Coordinates ({x}, {y}) are out of map boundaries."
            )
        character.cancel_path()
        character.set_position((x, y))
