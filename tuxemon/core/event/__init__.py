# -*- coding: utf-8 -*-
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
    """ Gets an NPC object by slug.  None is returned if not found.

    Pass "player" to get the player's entity of this session.
    Name is outdated.  Will return any live game object by the slug.

    :param tuxemon.core.session.Session session: The session object
    :param str slug: The slug of the NPC that exists on the current map.
    :rtype: Optional[tuxemon.core.player.Player]
    """
    if slug == "player":
        return session.player
    return session.world.get_entity(slug)
