#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventcondition import EventCondition


def entity_at_position(entity, event):
    """
    Only true if the entity is exactly in the center of the tile.
    Partially in/out the tile will be False.
    """
    return event.rect.topleft == entity.tile_pos


class NPCAtCondition(EventCondition):
    """ Checks to see if an npc is at a current position on the map.
    """

    name = "npc_at"

    def test(self, session, event, condition):
        entity = get_npc(session, condition.parameters[0])
        return entity_at_position(entity, event)


class PlayerAtCondition(EventCondition):
    """ Checks to see if an npc is at a current position on the map.
    """

    name = "player_at"

    def test(self, session, event, condition):
        return entity_at_position(session.player, event)
