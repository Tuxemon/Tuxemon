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

import logging
from collections import namedtuple
from dataclasses import dataclass

from tuxemon.compat import Rect

logger = logging.getLogger(__name__)

# Set up map action and condition objects
condition_fields = [
    "name",
    "operator",
    "parameters",
]

action_fields = ["type", "parameters"]


MapCondition = namedtuple("condition", condition_fields)
MapAction = namedtuple("action", action_fields)

# event_fields = ["id", "name", "rect", "conds", "acts"]
# EventObject = namedtuple("eventobject", event_fields)


@dataclass(frozen=True, order=True)
class EventObject:
    id: str
    name: str
    rect: Rect
    conds: list
    acts: list


__all__ = ["EventObject", "MapAction", "MapCondition", "get_npc"]


def get_npc(context, slug):
    """Gets an NPC object by slug.  None is returned if not found.

    Pass "player" to get the player's entity of this session.

    :param tuxemon.event.eventengine.EventContext context
    :param str slug: The slug of the NPC that exists on the current map.
    :rtype: Optional[tuxemon.npc.NPC]
    """
    if slug == "player":
        return context.player
    return context.world.get_entity(slug)
