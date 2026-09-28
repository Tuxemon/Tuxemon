# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Tuxemon server and client."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING, Any

from tuxemon.db import Direction
from tuxemon.item.item import decode_items, encode_items
from tuxemon.monster.monster import decode_monsters, encode_monsters
from tuxemon.session import local_session
from tuxemon.states import world_state as world

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    PUSH_SELF = "PUSH_SELF"
    CLIENT_MOVE_START = "CLIENT_MOVE_START"
    CLIENT_MAP_UPDATE = "CLIENT_MAP_UPDATE"
    CLIENT_MOVE_COMPLETE = "CLIENT_MOVE_COMPLETE"
    CLIENT_KEYDOWN = "CLIENT_KEYDOWN"
    CLIENT_KEYUP = "CLIENT_KEYUP"
    CLIENT_FACING = "CLIENT_FACING"
    CLIENT_INTERACTION = "CLIENT_INTERACTION"
    CLIENT_RESPONSE = "CLIENT_RESPONSE"
    CLIENT_START_BATTLE = "CLIENT_START_BATTLE"
    CLIENT_DISCONNECTED = "CLIENT_DISCONNECTED"
    PING = "PING"
    SERVER_SHUTDOWN = "SERVER_SHUTDOWN"


@dataclass
class CharData:
    """Represents the mutable state of a character payload."""

    tile_pos: tuple[
        int, int
    ]  # (x, y) position of the character on the map grid
    name: str  # Character's display name
    facing: Direction  # Direction the character is currently facing (e.g., up, down)
    running: bool = False
    monsters: list[Monster] = field(
        default_factory=list
    )  # List of monsters the character owns
    inventory: list[Item] = field(
        default_factory=list
    )  # List of items in the character's inventory

    def copy(self, **updates: Any) -> CharData:
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tile_pos": self.tile_pos,
            "name": self.name,
            "facing": self.facing.name,
            "running": self.running,
            "monsters": encode_monsters(self.monsters),
            "inventory": encode_items(self.inventory),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CharData:
        return CharData(
            tile_pos=tuple(data["tile_pos"]),
            name=data["name"],
            facing=Direction[data["facing"]],
            running=bool(data["running"]),
            monsters=decode_monsters(data.get("monsters", [])),
            inventory=decode_items(data.get("inventory", [])),
        )


@dataclass
class EventData:
    """Represents the network event payload sent between client and server."""

    type: EventType  # The type of event (e.g., CLIENT_KEYDOWN, PUSH_SELF)
    event_number: int  # Sequence number for tracking event order
    cuuid: str | None = (
        None  # Unique client identifier (who sent or triggered the event)
    )
    direction: str | None = (
        None  # Intended movement direction (e.g., "up", "left") — used in movement events
    )
    interaction: str | None = (
        None  # Type of interaction (e.g., "talk", "battle") — used in interaction events
    )
    map_name: str | None = None  # Name of the map where the event occurred
    char_dict: CharData | None = (
        None  # Snapshot of character state (position, facing, inventory, etc.)
    )
    kb_key: str | None = (
        None  # Key pressed or released (e.g., "SHIFT", "up") — used in input events
    )
    target: str | None = (
        None  # Target client or entity for interactions or combat
    )
    response: Any | None = (
        None  # Optional response payload (e.g., dialogue result, battle outcome)
    )

    def copy(self, **updates: Any) -> EventData:
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.name,
            "event_number": self.event_number,
            "cuuid": self.cuuid,
            "interaction": self.interaction,
            "map_name": self.map_name,
            "char_dict": self.char_dict.to_dict() if self.char_dict else None,
            "kb_key": self.kb_key,
            "target": self.target,
            "response": self.response,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> EventData:
        return EventData(
            type=EventType[data["type"]],
            event_number=data["event_number"],
            cuuid=data.get("cuuid"),
            interaction=data.get("interaction"),
            map_name=data.get("map_name"),
            char_dict=(
                CharData.from_dict(data["char_dict"])
                if data.get("char_dict")
                else None
            ),
            kb_key=data.get("kb_key"),
            target=data.get("target"),
            response=data.get("response"),
        )


def populate_client(
    cuuid: str,
    event_data: EventData,
    game: BaseClient,
    registry: dict[str, dict[str, Any]],
) -> NPC:
    """
    Creates an NPC to represent the client character and adds the information
    to the registry.

    Parameters:
        cuuid (str): The unique user identification number for the client.
        event_data (EventData): Event information sent by the client,
            containing details about the client character (e.g., sprite name,
            map name, and character dictionary).
        game: The game control object for managing the server or client.
        registry: A registry containing client information on the server or client.

    Returns:
        The sprite representing the client character.
    """
    if event_data.char_dict is None or event_data.map_name is None:
        raise ValueError(f"Incomplete event data for client {cuuid}")

    char_data = event_data.char_dict
    char_name = char_data.name
    tile_pos_x, tile_pos_y = char_data.tile_pos

    # Create the NPC sprite based on the provided information
    game.event_engine.execute_action(
        "create_npc", [char_name, tile_pos_x, tile_pos_y]
    )
    char = local_session.client.get_npc(char_name)
    if char is None:
        raise RuntimeError(f"Failed to create or retrieve NPC for {char_name}")

    char.is_player = True
    char._last_tile_pos = char.tile_pos
    char.interactions = ["TRADE", "DUEL"]

    # Update the registry with the client sprite and map name
    registry[cuuid]["sprite"] = char
    registry[cuuid]["map_name"] = event_data.map_name

    return char


def update_client(
    sprite: NPC, char_data: CharData | None, game: BaseClient
) -> None:
    """Corrects character location when it changes map or loses sync.

    Updates a client's character information, correcting its location and
    synchronization when switching maps or when data becomes out of sync.

    Parameters:
        sprite: The NPC object representing the local client's character
            (stored in the registry).
        char_data: A CharData object containing updated character state (e.g., tile position, facing).
        game: The game control object (server or client) for managing the game's state.
    """
    # Functionality is incomplete due to lack of global x/y implementation
    return
    if char_data is None:
        return

    # Get the game world state
    world_state = game.get_state_by_name(world.WorldState)

    # Convert CharData to dictionary
    data = char_data.to_dict()

    # Update sprite attributes
    for item, value in data.items():
        sprite.__dict__[item] = value

        # Handle tile position updates
        if item == "tile_pos":
            tile_size = game.context.tile_size
            position = [
                value[0] * tile_size[0],
                value[1] * tile_size[1],
            ]
            global_x = getattr(world_state, "global_x", 0)
            global_y = getattr(world_state, "global_y", 0)
            abs_position = [
                position[0] + global_x,
                position[1] + (global_y - tile_size[1]),
            ]
            sprite.__dict__["position"] = abs_position
