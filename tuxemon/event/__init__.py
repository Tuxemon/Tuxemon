# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import namedtuple
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence

from tuxemon.session import Session

if TYPE_CHECKING:
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


__all__ = ["EventObject", "MapAction", "MapCondition", "get_npc"]


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

    # Loop through the NPC list and see if the slug matches any in the list
    world = session.client.get_state_by_name(WorldState)

    # logger.error("Unable to find NPC: " + slug)
    return world.get_entity(slug)
