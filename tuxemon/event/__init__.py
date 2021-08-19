#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#

from __future__ import annotations
import logging
from collections import namedtuple
from typing import NamedTuple, Sequence, Optional, TYPE_CHECKING
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
    name: str


class MapAction(NamedTuple):
    type: str
    parameters: Sequence[str]
    name: str


class EventObject(NamedTuple):
    id: int
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
        session: The session object
        slug: The slug of the NPC that exists on the current map.

    Returns:
        The NPC object or None if the NPC is not found.

    """
    if slug == "player":
        return session.player

    # Loop through the NPC list and see if the slug matches any in the list
    world = session.client.get_state_by_name("WorldState")
    if world is None:
        logger.error("Cannot search for NPC if world doesn't exist: " + slug)
        return None

    # logger.error("Unable to find NPC: " + slug)
    return world.get_entity(slug)
