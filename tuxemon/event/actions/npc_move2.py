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

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_direction, dirs3, dirs2
from tuxemon.npc import tile_distance
from tuxemon.tools import trunc


class NpcMoveTileAction(EventAction):
    name = "npc_move_tile"

    def __init__(self, *args, **kwrags):
        super().__init__(*args, **kwrags)
        self.npc = None
        self.path = None
        self.path_origin = None

    def start(self):
        npc_slug = self.raw_parameters[0]
        direction = self.raw_parameters[1]
        self.npc = get_npc(self.context, npc_slug)
        self.npc.velocity3 = self.npc.moverate * dirs3[direction]

    def update(self):
        time_passed_seconds = 0.016
        self.update_physics(time_passed_seconds)

        # if self.path_origin:
        #     self.check_waypoint()
        # elif self.path:
        #     self.next_waypoint()

    def check_continue(self):
        try:
            pos = tuple(int(i) for i in self.tile_pos)
            direction_next = self.map.collision_map[pos]["continue"]
            self.move_one_tile(direction_next)
        except (KeyError, TypeError):
            pass

    def cancel_path(self):
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self):
        self._move_direction = None
        if self.tile_pos == self.path_origin:
            # we *just* started a new path; discard it and stop
            self.abort_movement()
        elif self.path and self.moving:
            # we are in the middle of moving between tiles
            self.path = [self.path[-1]]
            self.pathfinding = None
        else:
            # probably already stopped, just clear the path
            self.stop_moving()
            self.cancel_path()

    def abort_movement(self):
        if self.path_origin is not None:
            self.tile_pos = tuple(self.path_origin)
        self._move_direction = None
        self.stop_moving()
        self.cancel_path()

    def move_one_tile(self, direction):
        self.path.append(trunc(self.tile_pos + dirs2[direction]))

    def valid_movement(self, tile):
        return True
        return tile in self.map.get_exits(trunc(self.tile_pos)) or self.ignore_collisions

    @property
    def move_destination(self):
        if self.path:
            return self.path[-1]
        else:
            return None

    def next_waypoint(self):
        target = self.path[-1]
        direction = get_direction(self.npc.tile_pos, target)
        self.facing = direction
        if self.valid_movement(target):
            self.path_origin = tuple(self.npc.tile_pos)
            self.npc.velocity3 = self.npc.moverate * dirs3[direction]
        else:
            # the target is blocked now
            self.stop_moving()

            if self.pathfinding:
                # since we are pathfinding, just try a new path
                self.pathfind(self.pathfinding)

            else:
                # give up and wait until the target is clear again
                pass

    def check_waypoint(self):
        target = self.path[-1]
        expected = tile_distance(self.path_origin, target)
        traveled = tile_distance(self.npc.tile_pos, self.path_origin)
        if traveled >= expected:
            self.set_position(target)
            self.path.pop()
            self.path_origin = None
            if self.path:
                self.next_waypoint()

    def stop_moving(self):
        """Completely stop all movement

        :return: None
        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def pos_update(self):
        """WIP.  Required to be called after position changes

        :return:
        """
        from tuxemon.world import proj

        self.npc.tile_pos = proj(self.npc.position3)

    def update_physics(self, td):
        """Move the entity according to the movement vector

        :param td:
        :return:
        """
        self.npc.position3 += self.npc.velocity3 * td
        self.pos_update()

    def set_position(self, pos):
        """Set the entity's position in the game world

        :param pos:
        :return:
        """
        self.npc.position3.x = pos[0]
        self.npc.position3.y = pos[1]
        self.pos_update()
