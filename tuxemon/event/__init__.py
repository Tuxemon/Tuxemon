# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple, Optional

from tuxemon.session import Session

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class MapCondition(NamedTuple):
    type: str
    parameters: Sequence[str]
    x: int
    y: int
    width: int
    height: int
    operator: str
    name: Optional[str]


class MapAction(NamedTuple):
    type: str
    parameters: Sequence[str]
    name: Optional[str]


class EventObject(NamedTuple):
    id: Optional[int]
    name: str
    x: int
    y: int
    w: int
    h: int
    conds: Sequence[MapCondition]
    acts: Sequence[MapAction]


__all__ = [
    "EventObject",
    "MapAction",
    "MapCondition",
    "get_npc",
    "get_npc_by_iid",
    "get_npc_pos",
    "get_monster_by_iid",
]


def get_npc(session: Session, slug: str) -> Optional[NPC]:
    """
    Gets an NPC object by slug.

    Parameters:
        session: The session object.
        slug: The slug of the NPC that exists on the current map.

    Returns:
        The NPC object or None if the NPC is not found.

    """
    from tuxemon.states.world.worldstate import WorldState

    if slug == "player":
        return session.player

    world = session.client.get_state_by_name(WorldState)

    return world.get_entity(slug)


def get_npc_by_iid(session: Session, iid: uuid.UUID) -> Optional[NPC]:
    """
    Gets an NPC object by iid.

    Parameters:
        session: The session object.
        iid: The iid of the NPC that exists on the current map.

    Returns:
        The NPC object or None if the NPC is not found.

    """
    from tuxemon.states.world.worldstate import WorldState

    world = session.client.get_state_by_name(WorldState)

    return world.get_entity_by_iid(iid)


def get_npc_pos(session: Session, pos: tuple[int, int]) -> Optional[NPC]:
    """
    Gets an NPC object by location (x,y).

    Parameters:
        session: The session object.
        pos: The position of the NPC on the current map (x,y).

    Returns:
        The NPC object or None if the NPC is not found.

    """
    from tuxemon.states.world.worldstate import WorldState

    player = session.player
    if player.tile_pos == pos:
        return session.player

    world = session.client.get_state_by_name(WorldState)

    return world.get_entity_pos(pos)


def get_monster_by_iid(session: Session, iid: uuid.UUID) -> Optional[Monster]:
    """
    Gets a monster object by iid among all the entities.

    Parameters:
        session: The session object.
        iid: The iid of the monster that exists on the current map.

    Returns:
        The monster object or None if the monster is not found.

    """
    from tuxemon.states.world.worldstate import WorldState

    world = session.client.get_state_by_name(WorldState)

    return world.get_monster_by_iid(iid)


def collide(condition: MapCondition, tile_position: tuple[int, int]) -> bool:
    """
    Check collision of a tile position with the map condition position.

    Parameters:
        condition: The map condition object.
        tile_position: A particular tile position.

    Returns:
        Whether the tile position is contained in the map condition area.

    """
    return (
        condition.x < tile_position[0] + 1
        and condition.y < tile_position[1] + 1
        and condition.x + condition.width > tile_position[0]
        and condition.y + condition.height > tile_position[1]
    )
