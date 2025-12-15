# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple, Optional
from uuid import UUID

from tuxemon.event.eventbus import EventBus
from tuxemon.session import Session

_GLOBAL_EVENT_BUS = EventBus()

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


__all__ = [
    "get_npc",
    "get_npc_by_iid",
    "get_npc_pos",
    "get_monster_by_iid",
    "get_event_bus",
]


def get_event_bus() -> EventBus:
    """
    Returns the global EventBus instance used for dispatching and listening
    to events throughout the application.

    This ensures a centralized event handling mechanism, allowing different
    parts of the system to communicate via published events and registered
    listeners.
    """
    return _GLOBAL_EVENT_BUS


def get_npc(session: Session, slug: str) -> Optional[NPC]:
    """
    Gets an NPC object by slug.

    Parameters:
        session: The session object.
        slug: The slug of the NPC that exists on the current map.

    Returns:
        The NPC object or None if the NPC is not found.
    """
    if slug == "player":
        return session.player

    return session.client.npc_manager.get_npc(slug)


def get_npc_by_iid(session: Session, iid: UUID) -> Optional[NPC]:
    """
    Gets an NPC object by iid.

    Parameters:
        session: The session object.
        iid: The iid of the NPC that exists on the current map.

    Returns:
        The NPC object or None if the NPC is not found.
    """
    return session.client.npc_manager.get_npc_by_iid(iid)


def get_npc_pos(session: Session, pos: tuple[int, int]) -> Optional[NPC]:
    """
    Gets an NPC object by location (x,y).

    Parameters:
        session: The session object.
        pos: The position of the NPC on the current map (x,y).

    Returns:
        The NPC object or None if the NPC is not found.
    """
    player = session.player
    if player.tile_pos == pos:
        return session.player

    return session.client.npc_manager.get_entity_pos(pos)


def get_monster_by_iid(session: Session, iid: UUID) -> Optional[Monster]:
    """
    Gets a monster object by iid among all the entities.

    Parameters:
        session: The session object.
        iid: The iid of the monster that exists on the current map.

    Returns:
        The monster object or None if the monster is not found.
    """
    return session.client.npc_manager.get_monster_by_iid(iid)
