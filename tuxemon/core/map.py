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
#
# core.map Game map module.
#
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from itertools import product
from math import pi, atan2, cos, sin

from tuxemon.compat import Rect
from tuxemon.core.euclid import Vector2, Vector3, Point2
from tuxemon.core.platform.const import intentions
from tuxemon.core.tools import round_to_divisible, nearest
from tuxemon.lib.bresenham import bresenham

logger = logging.getLogger(__name__)

# direction => vector3
dirs3 = {
    "up": Vector3(0, -1, 0),
    "down": Vector3(0, 1, 0),
    "left": Vector3(-1, 0, 0),
    "right": Vector3(1, 0, 0),
}

# direction => vector2
dirs2 = {
    "up": Vector2(0, -1),
    "down": Vector2(0, 1),
    "left": Vector2(-1, 0),
    "right": Vector2(1, 0),
}

# just the first letter of the direction => vector
short_dirs = {d[0]: dirs2[d] for d in dirs2}

# complimentary directions
pairs = {"up": "down", "down": "up", "left": "right", "right": "left"}

# translate input directions to strings we use
direction_map = {
    intentions.UP: "up",
    intentions.DOWN: "down",
    intentions.LEFT: "left",
    intentions.RIGHT: "right",
}

# what directions entities can face
facing = "front", "back", "left", "right"


def translate_short_path(path, position=(0, 0)):
    """ Translate condensed path strings into coordinate pairs

    Uses a string of U D L R characters; Up Down Left Right.
    Passing a position will make the path relative to that point.

    :param path: string of path directions; ie "uldr"
    :type path: str
    :param position: starting point of the path

    :return: list
    """
    position = Point2(*position)
    for char in path.lower():
        position += short_dirs[char]
        yield position


def get_direction(base, target):
    y_offset = base[1] - target[1]
    x_offset = base[0] - target[0]
    # Is it further away vertically or horizontally?
    look_on_y_axis = abs(y_offset) >= abs(x_offset)

    if look_on_y_axis:
        return "up" if y_offset > 0 else "down"
    else:
        return "left" if x_offset > 0 else "right"


def proj(point):
    """ Project 3d coordinates to 2d.

    Not necessarily for use on a screen.

    :param point:

    :rtype: Tuple[Float, Float]
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


def tiles_inside_rect(rect, grid_size):
    """ Iterate all tile positions within this rect from left to right, top to bottom

    :param Rect rect: area to get tiles in
    :param Tuple[int, int] grid_size: size of each tile
    :rtype: Iterator[Tuple[int, int]]
    """
    for y, x in product(
        range(rect.top, rect.bottom, grid_size[1]),
        range(rect.left, rect.right, grid_size[0]),
    ):
        yield x // grid_size[0], y // grid_size[1]


def snap_to_grid(point, grid_size):
    """ Snap point to nearest grid intersection

    :param Tuple[int, int] point: point to snap
    :param Tuple[int, int] grid_size: grid size
    :rtype: Tuple[int, int]
    """
    return (
        round_to_divisible(point[0], grid_size[0]),
        round_to_divisible(point[1], grid_size[1]),
    )


def snap_to_tile(point, grid_size):
    """ Snap pixel coordinate to grid, then convert to tile coords

    :param point:
    :param grid_size:
    :rtype: Tuple[int, int]
    """
    point = snap_to_grid(point, grid_size)
    return point[0] // grid_size[0], point[1] // grid_size[1]


def snap_rect_to_grid(rect, grid_size):
    """ Align all vertices to the nearest point on grid

    :param Rect rect:
    :param Tuple[int, int] grid_size:
    :rtype: Rect
    """
    left, top = snap_to_grid(rect.topleft, grid_size)
    right, bottom = snap_to_grid(rect.bottomright, grid_size)
    return Rect((left, top), (right - left, bottom - top))


def snap_rect_to_tile(rect, grid_size):
    """ Align all vertices to the nearest point on grid, then convert to tile coords

    :param Rect rect:
    :param Tuple[int, int] grid_size:
    :rtype: Rect
    """
    left, top = snap_to_tile(rect.topleft, grid_size)
    right, bottom = snap_to_tile(rect.bottomright, grid_size)
    return Rect((left, top), (right - left, bottom - top))


def angle_of_points(point0, point1):
    """ Find angle between two points

    :param Tuple[int, int] point0:
    :param Tuple[int, int] point1:
    :rtype: Float
    """
    ang = atan2(-(point1[1] - point0[1]), point1[0] - point1[0])
    ang %= 2 * pi
    return ang


def orientation_by_angle(angle):
    """ Return "horizontal" or "vertical"

    :param Float angle:
    :rtype: str
    """
    angle %= 2 * pi
    if angle == 3 / 2 * pi:
        return "vertical"
    elif angle == 0.0:
        return "horizontal"
    else:
        raise Exception("A collision line must be aligned to an axis")


def tiles_along_line(points, tile_size):
    """ Identify the tiles on either side of the line

    Lines must be exactly horizontal or vertical and have exactly two points.
    Points will be snapped to nearest tile.

    Iterate Tuple[ "Side 1 Tile", "Side 2 Tile", "Orientation" ]
    Where Side 1 will be the Left or Top tile, and Side 2 will be the
    Right or Bottom tile.  Orientation will be either "horizontal" or
    "vertical".

    :param List[Tuple] points: Exactly two Tuple[int, int] for each point of line segment
    :param Tuple [int, int] tile_size:
    :return: Iterator[Tuple[Tuple[int, int], Tuple[int, int], str]]
    """
    if len(points) != 2:
        raise ValueError("Error: collision lines must be exactly 2 points")
    p0 = snap_to_tile(points[0], tile_size)
    p1 = snap_to_tile(points[1], tile_size)
    p0, p1 = sorted((p0, p1))
    angle = angle_of_points(p0, p1)
    orientation = orientation_by_angle(angle)
    for i in bresenham(p0[0], p0[1], p1[0], p1[1], include_end=False):
        angle1 = angle - (pi / 2)
        other = int(round(cos(angle1) + i[0])), int(round(sin(angle1) + i[1]))
        yield i, other, orientation


class PathfindNode(object):
    """ Used in path finding search
    """

    def __init__(self, value, parent=None):
        self.parent = parent
        self.value = value
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent
        self.depth = parent.depth + 1

    def get_value(self):
        return self.value

    def get_depth(self):
        return self.depth

    def __str__(self):
        s = str(self.value)
        if self.parent is not None:
            s += str(self.parent)
        return s


class TuxemonMap(object):
    """
    Contains collisions geometry and events

    Supports entity movement and pathfinding
    """

    def __init__(
        self,
        events,
        inits,
        interacts,
        collision_map,
        collisions_lines_map,
        data,
        edges,
        filename,
    ):
        """ Constructor

        Collision lines:
        Player can walk in tiles, but cannot cross from one to another. Items
        in this list should be in the form of pairs, signifying that it is NOT
        possible to travel from the first tile to the second (but reverse may
        be possible, i.e. jumping) All pairs of tiles must be adjacent (not
        diagonal)

        Collision Lines Map:
        Create a list of all pairs of adjacent tiles that are impassable (aka walls)
        example: ((5,4),(5,3), both)

        :param List events: List of map events
        :param List inits: List of events to be loaded once, when map is entered
        :param List interacts: List of intractable spaces
        :param Dict collision_map: Collision map
        :param Dict collisions_lines_map: Collision map of lines
        """
        self.interacts = interacts
        self.collision_map = collision_map
        self.collision_lines_map = collisions_lines_map
        self.npcs = dict()
        self.size = data.width, data.height
        self.inits = inits
        self.events = events
        self.renderer = None
        # TODO: create conditions to clamp the edges according to map/screen size
        self.edges = edges
        self.clamped = self.edges == "clamped"
        self.data = data
        self.sprite_layer = 2
        self.filename = filename
        # TODO: remove this invalid_xxx hack
        self.invalid_x = (-1, self.size[0])
        self.invalid_y = (-1, self.size[1])

    def pathfind(self, start, dest):
        """ Pathfind

        :param start:
        :type dest: tuple

        :return:
        """
        pathnode = self.pathfind_r(dest, [PathfindNode(start)], set(),)

        if pathnode:
            # traverse the node to get the path
            path = []
            while pathnode:
                path.append(pathnode.get_value())
                pathnode = pathnode.get_parent()

            return path[:-1]

        else:
            # TODO: get current map name for a more useful error
            logger.error(
                "Pathfinding failed to find a path from "
                + str(start)
                + " to "
                + str(dest)
                + ". Are you sure that an obstacle-free path exists?"
            )

    def pathfind_r(self, dest, queue, known_nodes):
        """ Breadth first search algorithm

        :type dest: tuple
        :type queue: list
        :type known_nodes: set

        :rtype: list
        """
        # The collisions shouldn't have changed whilst we were calculating,
        # so it saves time to reuse the map.
        collision_map = self.get_collision_map()
        while queue:
            node = queue.pop(0)
            if node.get_value() == dest:
                return node
            else:
                for adj_pos in self.get_exits(
                    node.get_value(), collision_map, known_nodes
                ):
                    new_node = PathfindNode(adj_pos, node)
                    known_nodes.add(new_node.get_value())
                    queue.append(new_node)

    def get_exits(self, position, collision_map=None, skip_nodes=None):
        """ Return list of tiles which can be moved into

        This checks for adjacent tiles while checking for walls, NPCs,
        collision lines, one-way tiles, etc

        :param position: tuple
        :param collision_map: dict
        :param skip_nodes: set
        :rtype: list
        """
        # get tile-level and npc/entity blockers
        if collision_map is None:
            collision_map = self.get_collision_map()

        if skip_nodes is None:
            skip_nodes = set()

        # if there are explicit way to exit this position use that information,
        # handles 'continue' and 'exits'
        tile_data = collision_map.get(position)
        if tile_data:
            exits = self.get_explicit_tile_exits(position, tile_data, skip_nodes)
        else:
            exits = None

        # get exits by checking surrounding tiles
        adjacent_tiles = list()
        for direction, neighbor in (
            ("down", (position[0], position[1] + 1)),
            ("right", (position[0] + 1, position[1])),
            ("up", (position[0], position[1] - 1)),
            ("left", (position[0] - 1, position[1])),
        ):
            # if exits are defined make sure the neighbor is present there
            if exits and neighbor not in exits:
                continue

            # check if the neighbor region is present in skipped nodes
            if neighbor in skip_nodes:
                continue

            # We only need to check the perimeter,
            # as there is no way to get further out of bounds
            # TODO: remove this somehow
            if neighbor[0] in self.invalid_x or neighbor[1] in self.invalid_y:
                continue

            # check to see if this tile is separated by a wall
            if (position, direction) in self.collision_lines_map:
                # there is a wall so stop checking this direction
                continue

            # test if this tile has special movement handling
            # NOTE: Do not refact. into a dict.get(xxxxx, None) style check
            # NOTE: None has special meaning in this check
            try:
                tile_data = collision_map[neighbor]
            except KeyError:
                pass
            else:
                # None means tile is blocked with no specific data
                if tile_data is None:
                    continue

                try:
                    if pairs[direction] not in tile_data["enter"]:
                        continue
                except KeyError:
                    continue

            # no tile data, so assume it is free to move into
            adjacent_tiles.append(neighbor)

        return adjacent_tiles

    def get_collision_map(self):
        """ Return dictionary for collision testing

        Returns a dictionary where keys are (x, y) tile tuples and the values
        are tiles or NPCs.

        :rtype: dict
        :returns: A dictionary of collision tiles
        """
        collision_dict = dict()

        # # Get all the NPCs' tile positions
        # for npc in self.get_all_entities():
        #     pos = nearest(npc.tile_pos)
        #     collision_dict[pos] = {"entity": npc}

        # tile layout takes precedence
        collision_dict.update(self.collision_map)

        return collision_dict

    @staticmethod
    def get_explicit_tile_exits(position, tile, skip_nodes):
        """ Check for exits from tile which are defined in the map

        Checks "continue" and "exits" properties of the tile

        :param Tuple[int, int] position: Tile position
        :param Dict tile: tile properties
        :param set skip_nodes: set of Tuples; nodes will be ignore as an exit
        :return: list
        """
        # does the tile define continue movements?
        try:
            return [tuple(dirs2[tile["continue"]] + position)]
        except KeyError:
            pass

        # does the tile explicitly define exits?
        try:
            adjacent_tiles = list()
            for direction in tile["exit"]:
                exit_tile = tuple(dirs2[direction] + position)
                if exit_tile not in skip_nodes:
                    adjacent_tiles.append(exit_tile)
            return adjacent_tiles
        except KeyError:
            pass
