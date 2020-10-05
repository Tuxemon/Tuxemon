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

import logging
from itertools import product
from math import pi, atan2

import pyscroll

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core.euclid import Vector2, Vector3, Point2
from tuxemon.core.tools import round_to_divisible

logger = logging.getLogger(__name__)

# direction => vector
dirs3 = {
    "up": Vector3(0, -1, 0),
    "down": Vector3(0, 1, 0),
    "left": Vector3(-1, 0, 0),
    "right": Vector3(1, 0, 0),
}
dirs2 = {
    "up": Vector2(0, -1),
    "down": Vector2(0, 1),
    "left": Vector2(-1, 0),
    "right": Vector2(1, 0),
}
# just the first letter of the direction => vector
short_dirs = {d[0]: dirs2[d] for d in dirs2}

# complimentary directions
pairs = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left"
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

    :return: tuple
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


def tiles_inside_rect(rect, grid_size):
    """ Iterate all tile positions within this rect

    The positions will be changed from pixel/map coords to tile coords

    :param Rect rect: area to get tiles in
    :param Tuple[int, int] grid_size: size of each tile
    :rtype: Iterator[Rect]
    """
    # scan order is left->right, top->bottom
    for y, x in product(
            range(rect.top, rect.bottom, grid_size[1]),
            range(rect.left, rect.right, grid_size[0]),
    ):
        yield x // grid_size[0], y // grid_size[1]


def snap_interval(value, interval):
    """

    :param Union[float, int] value:
    :param int interval:
    :rtype: int
    """
    value = round_to_divisible(value)
    if value == interval:
        return value - 1
    return value


def snap_outer_point(point, grid_size):
    """ Snap point to nearest grid intersection

    * If point is rounded up, the coords are 1 less on each axis

    :param Tuple[int, int] point: point to snap
    :param Tuple[int, int] grid_size: grid size
    :rtype: Tuple[int, int]
    """
    return (snap_interval(point[0], grid_size[0]),
            snap_interval(point[1], grid_size[1]))


def snap_point(point, grid_size):
    """ Snap point to nearest grid intersection

    :param Tuple[int, int] point: point to snap
    :param Tuple[int, int] grid_size: grid size
    :rtype: Tuple[int, int]
    """
    return (round_to_divisible(point[0], grid_size[0]),
            round_to_divisible(point[1], grid_size[1]))


def point_to_grid(point, grid_size):
    """ Snap pixel coordinate to grid, then convert to tile coords

    :param point:
    :param grid_size:
    :rtype: Tuple[int, int]
    """
    point = snap_point(point, grid_size)
    return point[0] // grid_size[0], point[1] // grid_size[1]


def angle_of_points(point0, point1):
    """ Find angle between two points

    :param Tuple[int, int] point0:
    :param Tuple[int, int] point1:
    :rtype: Float
    """
    ang = atan2(-(point1[1] - point0[1]), point1[0] - point1[0])
    ang %= 2 * pi
    return ang


def snap_rect(rect, grid_size):
    """ Align all vertices to the nearest point

    :param rect:
    :param grid_size:
    :return:
    """
    left, top = snap_point(rect.topleft, grid_size)
    right, bottom = snap_point(rect.bottomright, grid_size)
    return Rect((left, top), (right - left, bottom - top))


def orientation_by_angle(angle):
    """ Return "horizontal" or "vertical"

    :param Float angle:
    :rtype: str
    """
    if angle == 3 / 2 * pi:
        orientation = "vertical"
    elif angle == 0.0:
        orientation = "horizontal"
    else:
        raise Exception("A collision line must be aligned to an axis")
    return orientation


def extract_region_properties(region):
    # Loop through properties and create list of directions for each property
    props = dict()
    enter = []
    exit = []
    props["enter"] = enter
    props["exit"] = exit
    for key in region:
        if "enter" in key:
            enter.extend(region[key].split())
        elif "exit" in key:
            exit.extend(region[key].split())
        elif "continue" in key:
            props["continue"] = region[key]
    return props


class PathfindNode:
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


class TuxemonMap:
    """
    Contains collisions geometry and events loaded from a file

    Supports entity movement and pathfinding
    """

    def __init__(self, events, inits, interacts, collision_map, collisions_lines_map, raw_data, edges, filename):
        """ Constructor

        Collision lines
        Player can walk in tiles, but cannot cross
        from one to another. Items in this list should be in the
        form of pairs, signifying that it is NOT possible to travel
        from the first tile to the second (but reverse may be
        possible, i.e. jumping) All pairs of tiles must be adjacent
        (not diagonal)

        Collision Lines Map
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
        self.size = raw_data.width, raw_data.height
        self.inits = inits
        self.events = events
        self.renderer = None
        self.edges = edges
        self.data = raw_data
        self.sprite_layer = 2
        self.filename = filename

    def initialize_renderer(self):
        """ Initialize the renderer for the map and sprites

        :rtype: pyscroll.BufferedRenderer
        """
        # TODO: Use self.edges == "stitched" here when implementing seamless maps
        visual_data = pyscroll.data.TiledMapData(self.data)
        clamp = (self.edges == "clamped")
        self.renderer = pyscroll.BufferedRenderer(visual_data, prepare.SCREEN_SIZE, clamp_camera=clamp, tall_sprites=2)

    def pathfind(self, start, dest):
        """ Pathfind

        :param start:
        :type dest: tuple

        :return:
        """
        pathnode = self.pathfind_r(
            dest,
            [PathfindNode(start)],
            set(),
        )

        if pathnode:
            # traverse the node to get the path
            path = []
            while pathnode:
                path.append(pathnode.get_value())
                pathnode = pathnode.get_parent()

            return path[:-1]

        else:
            # TODO: get current map name for a more useful error
            logger.error("Pathfinding failed to find a path from " +
                         str(start) + " to " + str(dest) +
                         ". Are you sure that an obstacle-free path exists?")

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
                for adj_pos in self.get_exits(node.get_value(), collision_map, known_nodes):
                    new_node = PathfindNode(adj_pos, node)
                    known_nodes.add(new_node.get_value())
                    queue.append(new_node)

    def get_explicit_tile_exits(self, position, tile, skip_nodes):
        """ Check for exits from tile which are defined in the map

        This will return exits which were defined by the map creator

        Checks "continue" and "exits" properties of the tile

        :param position: tuple
        :param tile:
        :param skip_nodes: set
        :return: list
        """
        # Check if the players current position has any exit limitations.
        # this check is for tiles which define the only way to exit.
        # for instance, one-way tiles.

        # does the tile define continue movements?
        try:
            return [tuple(dirs2[tile['continue']] + position)]
        except KeyError:
            pass

        # does the tile explicitly define exits?
        try:
            adjacent_tiles = list()
            for direction in tile["exit"]:
                exit_tile = tuple(dirs2[direction] + position)
                if exit_tile in skip_nodes:
                    continue

                adjacent_tiles.append(exit_tile)
            return adjacent_tiles
        except KeyError:
            pass

    def get_pos_from_tilepos(self, tile_position):
        """ Returns the map pixel coordinate based on tile position.

        USE this to draw to the screen

        :param tile_position: An [x, y] tile position.

        :type tile_position: List

        :rtype: List
        :returns: The pixel coordinates to draw at the given tile position.
        """
        cx, cy = self.current_map.renderer.get_center_offset()
        px, py = self.project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def _collision_box_to_rect(self, box):
        """Returns a pygame.Rect (in screen-coords) version of a collision box (in world-coords).
        """

        # For readability
        x, y = self.get_pos_from_tilepos(box)
        tw, th = self.tile_size

        return Rect(x, y, tw, th)

    def _npc_to_rect(self, npc):
        """Returns a pygame.Rect (in screen-coords) version of an NPC's bounding box.
        """
        pos = self.get_pos_from_tilepos(npc.tile_pos)
        return Rect(pos, self.tile_size)
