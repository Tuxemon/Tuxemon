# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from tuxemon.db import Direction

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.map.transition import MapTransition
    from tuxemon.npc_manager import NPCManager
    from tuxemon.save_system.save_state import NPCState
    from tuxemon.state.manager import StateManager

logger = logging.getLogger(__name__)


@dataclass
class TeleportFaint:
    map_name: str = "default.tmx"
    x: int = 0
    y: int = 0

    @classmethod
    def from_dict(cls, data: NPCState) -> TeleportFaint:
        raw = data.teleport_faint

        if raw is None:
            return cls()

        if isinstance(raw, tuple):
            keys = ["map_name", "x", "y"]
            mapped = dict(zip(keys, raw))
        elif isinstance(raw, Mapping):
            mapped = dict(raw)
        else:
            # Unexpected format—fallback to empty
            mapped = {}

        return cls(
            map_name=mapped.get("map_name", "default.tmx"),
            x=int(mapped.get("x", 0)),
            y=int(mapped.get("y", 0)),
        )

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "map_name": self.map_name,
            "x": self.x,
            "y": self.y,
        }

    def is_valid(self, map_name: str, x: int, y: int) -> bool:
        return self.map_name == map_name and self.x == x and self.y == y

    def is_default(self) -> bool:
        return self.map_name == "default.tmx" and self.x == 0 and self.y == 0


@dataclass
class TeleportRequest:
    char: NPC | None
    mapname: str
    x: int
    y: int
    facing: Direction | None = None
    source_map: str | None = None
    source_x: int | None = None
    source_y: int | None = None


class TeleportQueue:
    def __init__(self) -> None:
        self.queue: deque[TeleportRequest] = deque()

    def enqueue(self, request: TeleportRequest) -> None:
        self.queue.append(request)

    def dequeue(self) -> TeleportRequest | None:
        return self.queue.popleft() if self.queue else None

    def peek(self) -> TeleportRequest | None:
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
        map_transition: MapTransition,
        npc_manager: NPCManager,
        state_manager: StateManager,
    ) -> None:
        self.map_transition = map_transition
        self.npc_manager = npc_manager
        self.state_manager = state_manager
        self.teleport_queue = TeleportQueue()
        self.last_teleport_request: TeleportRequest | None = None

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
        self.map_transition.change_map(map_name)
        self.map_transition.validate_coordinates(x, y)
        self.npc_manager.place_npc_on_map(character, map_name, x, y)
        logger.debug(f"{character.slug} has completed teleportation.")

    def prepare_teleport(self, character: NPC) -> None:
        """
        Prepare the character for teleportation by stopping movement and
        locking controls.

        Parameters:
            character: The character to prepare for teleportation.
        """
        logger.debug(f"Preparing {character.slug} for teleportation...")

        if self.state_manager.is_in_base_map_state():
            self.state_manager.push_state_with_timeout("TeleporterState", 15)

        logger.info(f"{character.slug} is prepared for teleportation.")
