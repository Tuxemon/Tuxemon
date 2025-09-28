# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.db import Direction

if TYPE_CHECKING:
    from tuxemon.boundary import BoundaryChecker
    from tuxemon.map.map_manager import MapManager
    from tuxemon.map.map_transition import MapTransition
    from tuxemon.movement import MovementManager
    from tuxemon.npc import NPC
    from tuxemon.npc_manager import NPCManager
    from tuxemon.state.manager import StateManager

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


@dataclass
class TeleportRequest:
    char: Optional[NPC]
    mapname: str
    x: int
    y: int
    facing: Optional[Direction] = None
    source_map: Optional[str] = None
    source_x: Optional[int] = None
    source_y: Optional[int] = None


class TeleportQueue:
    def __init__(self) -> None:
        self.queue: deque[TeleportRequest] = deque()

    def enqueue(self, request: TeleportRequest) -> None:
        self.queue.append(request)

    def dequeue(self) -> Optional[TeleportRequest]:
        return self.queue.popleft() if self.queue else None

    def peek(self) -> Optional[TeleportRequest]:
        return self.queue[0] if self.queue else None

    def clear(self) -> None:
        self.queue.clear()

    def is_empty(self) -> bool:
        return not self.queue


class Teleporter:
    """
    Facilitates teleportation of characters within the game world.

    This class is responsible for instant and delayed teleportation of
    characters to specific locations. It ensures the smooth transition
    of characters between maps, handles screen state changes, and maintains
    game world consistency during teleportation.
    """

    def __init__(
        self,
        boundary: BoundaryChecker,
        map_manager: MapManager,
        map_transition: MapTransition,
        movement_manager: MovementManager,
        npc_manager: NPCManager,
        state_manager: StateManager,
    ) -> None:
        self.boundary = boundary
        self.map_manager = map_manager
        self.map_transition = map_transition
        self.movement_manager = movement_manager
        self.npc_manager = npc_manager
        self.state_manager = state_manager
        self.teleport_queue = TeleportQueue()
        self.last_teleport_request: Optional[TeleportRequest] = None

    def handle_next_teleport(self, character: NPC) -> None:
        request = self.teleport_queue.dequeue()
        if request:
            self.last_teleport_request = request
            self.execute_teleport(character, request)

    def execute_teleport(
        self, character: NPC, request: TeleportRequest
    ) -> None:
        self.teleport_character(
            request.char or character,
            request.mapname,
            request.x,
            request.y,
        )
        if request.facing:
            (request.char or character).set_facing(request.facing)

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
        self.movement_manager.stop_char(character)

        if len(self.state_manager.active_states) == 2:
            self.state_manager.push_state_with_timeout("TeleporterState", 15)

        self.movement_manager.lock_controls(character)
        logger.info(f"{character.slug} is prepared for teleportation.")

    def finalize_teleport(self, character: NPC) -> None:
        """
        Finalize the teleportation process by unlocking controls and resetting
        the character's state.

        Parameters:
            character: The character to finalize teleportation for.
        """
        logger.debug(f"Finalizing teleportation for {character.slug}...")
        self.movement_manager.unlock_controls(character)
        logger.info(f"{character.slug} has completed teleportation.")
        self.npc_manager.add_npc(character)

    def _switch_map_if_needed(self, map_name: str) -> None:
        if (
            self.map_manager.current_map is None
            or map_name != self.map_manager.current_map.filename
        ):
            target_map = fetch_asset("maps", map_name)
            if not target_map:
                raise ValueError(f"Map '{map_name}' does not exist.")
            self.map_transition.change_map(target_map)

    def _update_character_position(
        self, character: NPC, x: int, y: int
    ) -> None:
        if not self.boundary.is_within_boundaries((x, y)):
            raise ValueError(
                f"Coordinates ({x}, {y}) are out of map boundaries."
            )
        character.cancel_path()
        character.set_position((x, y))
