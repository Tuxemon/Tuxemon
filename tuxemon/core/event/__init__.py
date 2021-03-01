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

logger = logging.getLogger(__name__)

# Set up map action and condition objects
condition_fields = [
    "type",
    "parameters",
    "x",
    "y",
    "width",
    "height",
    "operator",
    "name"]

action_fields = [
    "type",
    "parameters",
    "name"]

event_fields = [
    "id",
    "name",
    "x",
    "y",
    "w",
    "h",
    "conds",
    "acts"]

MapCondition = namedtuple("condition", condition_fields)
MapAction = namedtuple("action", action_fields)
EventObject = namedtuple("eventobject", event_fields)

__all__ = [
    "EventObject",
    "MapAction",
    "MapCondition",
    "get_npc"
]


def get_npc(session, slug):
    """ Gets an NPC object by slug.

    :param session: The session object
    :param slug: The slug of the NPC that exists on the current map.

    :type session: tuxemon.core.session.Session
    :type slug: str

    :rtype: tuxemon.core.player.Player
    :returns: The NPC object or None if the NPC is not found.
    """
    if slug == "player":
        return session.player

    # Loop through the NPC list and see if the slug matches any in the list
    world = session.client.get_state_by_name("WorldState")
    if world is None:
        logger.error("Cannot search for NPC if world doesn't exist: " + slug)
        return

    # logger.error("Unable to find NPC: " + slug)
    return world.get_entity(slug)
