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

from tuxemon.core.event.eventcondition import EventCondition


# TODO: move to some other place?
def collide(condition, tile_position):
    """
    :type condition: tuxemon.core.event.MapCondition
    :param tile_position: tuple
    :rtype: bool
    """
    return condition.x < tile_position[0] + 1 \
           and condition.y < tile_position[1] + 1 \
           and condition.x + condition.width > tile_position[0] \
           and condition.y + condition.height > tile_position[1]


class PlayerMovedCondition(EventCondition):
    """Checks to see the player has just moved into this tile. Using this condition will
    prevent a condition like "player_at" from constantly being true every single frame.

    * Check if player destination collides with event
    * If it collides, wait until destination changes
    * Become True after collides and destination has changed

    These rules ensure that the event is true once player in in the tile
    and is only true once.  Could possibly be better, IDK.

    """
    name = "player_moved"

    def test(self, session,  condition):
        """Checks to see the player has just moved into this tile. Using this condition will
        prevent a condition like "player_at" from constantly being true every single frame.

        :type session: tuxemon.core.session.Session
        :type condition: tuxemon.core.event.MapCondition

        :rtype: bool

        Valid Parameters: None

        **Examples:**

        >>> condition.__dict__
        {
            "type": "player_moved",
            "parameters": [],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """
        # TODO: Eventually generalize command for checking players and npcs
        return self.generic_test(session, condition, session.player)

    def generic_test(self, session,  condition, npc):
        """ Eventually, this can be made into own condition or something

        :type session: tuxemon.core.session.Session
        :type condition: tuxemon.core.event.MapCondition

        :rtype: bool
        """
        # check where the npc is going, not where it is
        move_destination = npc.move_destination

        # a hash/id of sorts for the condition
        condition_str = str(condition)

        stopped = move_destination is None
        collide_next = False if stopped else collide(condition, move_destination)

        # persist is data shared for all player_moved EventConditions
        persist = self.get_persist(session)

        # only test if tile was moved into
        # get previous destination for this particular condition
        last_destination = persist.get(condition_str)
        if last_destination is None and (stopped or collide_next):
            persist[condition_str] = move_destination

        # has the npc moved onto or away from the event?
        # Check to see if the npc's "move destination" has changed since the last
        # frame. If it has, WE'RE MOVING!!!
        moved = move_destination != last_destination

        # is the npc colliding with the condition boundaries?
        collided = collide(condition, npc.tile_pos)

        # Update the current npc's last move destination
        # TODO: some sort of global tracking of player instead of recording it in conditions
        persist[condition_str] = move_destination

        # determine if the tile has truly changed
        if collided and moved and last_destination is not None:
            persist[condition_str] = None
            return True
        return False
