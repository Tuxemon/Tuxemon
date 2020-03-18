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
import re

import pyscroll
import pytmx
from pytmx.util_pygame import load_pygame
from natsort import natsorted

from tuxemon.core import prepare
from tuxemon.core.euclid import Vector2, Vector3, Point2
from tuxemon.core.event import EventObject
from tuxemon.core.event import MapAction
from tuxemon.core.event import MapCondition
from tuxemon.core.graphics import scaled_image_loader

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


class Tile(object):
    """A class to create tile objects. Tile objects are used to keep track of tile properties such
    as the layer it's on, its position, surface, and other properties.

    """

    def __init__(self, name, surface, tileset):
        self.name = name
        self.surface = surface
        self.layer = None
        self.type = None
        self.tileset = tileset


class Map(object):
    """Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/

    """

    def __init__(self, filename):
        self.filename = None
        self.data = None
        self.size = None
        self.renderer = None

        # Initiate the properties of the map at their default values
        self.edges = ""

        # Get the tile size from a tileset in our map. This is used to calculate the number of tiles
        # in a collision region.
        self.tile_size = (0, 0)

        # set the default layer to draw character sprites
        self.sprite_layer = 2

        # Collision tiles in tmx object format
        self.collisions = []

        # Collision lines (player can walk in tiles, but cannot cross
        # from one to another) Items in this list should be in the
        # form of pairs, signifying that it is NOT possible to travel
        # from the first tile to the second (but reverse may be
        # possible, i.e. jumping) All pairs of tiles must be adjacent
        # (not diagonal)
        self.collision_lines = []

        self.events = []
        self.inits = []
        self.interacts = []

        # Initialize the map
        self.load(filename)

    def load(self, filename):
        """Load map data from a tmx map file and get all the map's events and collision areas.
        Loading the map data is done using the pytmx library.

        Specifications for the TMX map format can be found here:
        https://github.com/bjorn/tiled/wiki/TMX-Map-Format

        **Examples:**

        In each map, there are three types of objects: **collisions**, **conditions**, and
        **actions**. Here is how an action would be defined using the Tiled map editor:

        .. image:: images/map/map_editor_action01.png

        :param filename: The path to the tmx map file to load.
        :type filename: String

        :rtype: None
        """
        self.filename = filename

        # Scale the loaded tiles if enabled
        if prepare.CONFIG.scaling:
            self.data = pytmx.TiledMap(filename,
                                       image_loader=scaled_image_loader,
                                       pixelalpha=True)
            self.data.tilewidth, self.data.tileheight = prepare.TILE_SIZE
        else:
            self.data = load_pygame(filename, pixelalpha=True)

        # Get the edge type of the map
        self.edges = self.data.properties.get("edges", "")
        # Get the layer to draw character sprites
        self.sprite_layer = int(self.data.properties.get("sprite_layer", 2))

        # make a scrolling renderer
        self.renderer = self.initialize_renderer()

        # Get the map dimensions
        self.size = self.data.width, self.data.height

        # Get the tile size of the map
        if self.data.tilesets:
            self.tile_size = self.data.tilesets[0].tilewidth, self.data.tilesets[0].tileheight
        else:
            self.tile_size = prepare.TILE_SIZE

        # Load all objects from the map file and sort them by their type.
        for obj in self.data.objects:
            if obj.type == 'collision':
                self.collisions.append(obj)

            elif obj.type == 'collision-line':
                self.collision_lines.append(obj)

            elif obj.type == 'event':
                self.events.append(self.loadevent(obj))

            elif obj.type == 'init':
                self.inits.append(self.loadevent(obj))

            elif obj.type == 'interact':
                self.interacts.append(self.loadevent(obj))

    def initialize_renderer(self):
        """ Initialize the renderer for the map and sprites

        :rtype: pyscroll.BufferedRenderer
        """
        # TODO: Use self.edges == "stitched" here when implementing seamless maps
        visual_data = pyscroll.data.TiledMapData(self.data)
        clamp = (self.edges == "clamped")
        return pyscroll.BufferedRenderer(visual_data, prepare.SCREEN_SIZE, clamp_camera = clamp, tall_sprites = 2)

    def loadevent(self, obj):
        """

        :param obj:
        :rtype: EventObject
        """

        conds = []
        acts = []

        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on..
        keys = natsorted(obj.properties.keys())

        x = int(obj.x / self.tile_size[0])
        y = int(obj.y / self.tile_size[1])
        w = int(obj.width / self.tile_size[0])
        h = int(obj.height / self.tile_size[1])

        for k in keys:
            if k.startswith('cond'):
                words = obj.properties[k].split(' ', 2)

                # Conditions have the form 'operator type parameters'.
                operator, cond_type = words[0:2]

                # If this condition has parameters, split them into a
                # list
                if len(words) > 2:
                    args = self.split_escaped(words[2])
                else:
                    args = list()

                # Create a condition object using named tuples
                condition = MapCondition(cond_type, args, x, y, w, h, operator, k)
                conds.append(condition)

            elif k.startswith('act'):
                words = obj.properties[k].split(' ', 1)

                # Actions have the form 'type parameters'.
                act_type = words[0]

                # If this action has parameters, split them into a
                # list
                if len(words) > 1:
                    args = self.split_escaped(words[1])
                else:
                    args = list()

                # Create an action object using named tuples
                action = MapAction(act_type, args, k)
                acts.append(action)

        for k in keys:
            if k.startswith('behav'):
                words = obj.properties[k].split(' ', 1)

                # Actions have the form 'type parameters'.
                behav_type = words[0]

                # If this action has parameters, split them into a
                # list
                if len(words) > 1:
                    args = self.split_escaped(words[1])
                else:
                    args = list()

                if behav_type == "talk":
                    conds.insert(0, MapCondition("to_talk", args, x, y, w, h, "is", k))
                    acts.insert(0, MapAction("npc_face", [args[0], "player"], k))

        # TODO: move this to some post-creation function, as more may be needed
        # add a player_facing_tile condition automatically
        if obj.type == "interact":
            cond_data = MapCondition("player_facing_tile", list(), x, y, w, h, "is", None)
            logger.debug(cond_data)
            conds.append(cond_data)

        return EventObject(obj.id, obj.name, x, y, w, h, conds, acts)

    def loadfile(self):
        """Loads the tile and collision data from the map file and returns a list of tiles with
        their position and pygame surface, a set of collision tile coordinates, and the size of
        the map itself. The list of tile surfaces is used to draw the map in the main game. The
        list of collision tile coordinates is used for collision detection.

        **Examples:**

        The list of tiles is structured in a way where you can access an individual tile by
        index number.

        The collision map is a set of (x,y) coordinates that the player cannot walk
        through. This set is generated based on collision regions defined in the
        map file.

        :rtype: List
        :returns: A multi-dimensional list of tiles in dictionary format; a set of collision
            coordinates; the map size.
        """
        # Get the dimensions of the map
        mapsize = self.size

        # Create a list of all tiles that we cannot walk through
        collision_map = {}

        # Create a list of all pairs of adjacent tiles that are impassable (aka walls)
        # example: ((5,4),(5,3), both)
        collision_lines_map = set()

        # Right now our collisions are defined in our tmx file as large regions that the player
        # can't pass through. We need to convert these areas into individual tile coordinates
        # that the player can't pass through.
        # Loop through all of the collision objects in our tmx file.
        for collision_region in self.collisions:

            # >>> collision_region.__dict__
            # {'gid': 0,
            # 'height': 16,
            # 'name': None,
            # 'parent': <TiledMap: "resources/maps/pallet_town-room.tmx">,
            # 'rotation': 0,
            # 'type': 'collision',
            # 'visible': 1,
            # 'width': 16,
            # 'x': 176,
            # 'y': 64}

            # Get the collision area's tile location and dimension in tiles using the tileset's
            # tile size.
            x = self.round_to_divisible(collision_region.x, self.tile_size[0]) / self.tile_size[0]
            y = self.round_to_divisible(collision_region.y, self.tile_size[1]) / self.tile_size[1]
            width = self.round_to_divisible(collision_region.width, self.tile_size[0]) / self.tile_size[0]
            height = self.round_to_divisible(collision_region.height, self.tile_size[1]) / self.tile_size[1]

            # Loop through properties and create list of directions for each property
            if collision_region.properties:
                enters = []
                exits = []

                for key in collision_region.properties:
                    if "enter" in key:
                        for direction in collision_region.properties[key].split():
                            enters.append(direction)
                    elif "exit" in key:
                        for direction in collision_region.properties[key].split():
                            exits.append(direction)

            # Loop through the area of this region and create all the tile coordinates that are
            # inside this region.
            for a in range(0, int(width)):
                for b in range(0, int(height)):
                    collision_tile = (a + x, b + y)
                    collision_map[collision_tile] = None

                    # Check if collision region has properties, and is therefore a conditional zone
                    # then add the location and conditions to semi_collision_map
                    if collision_region.properties:
                        tile_conditions = {}
                        for key in collision_region.properties.keys():
                            if "enter" in key:
                                tile_conditions['enter'] = enters
                            if "exit" in key:
                                tile_conditions['exit'] = exits
                            if "continue" in key:
                                tile_conditions['continue'] = collision_region.properties[key]
                        collision_map[collision_tile] = tile_conditions

        # Similar to collisions, except we need to identify the tiles
        # on either side of the poly-line and prevent moving between
        # them
        for collision_line in self.collision_lines:

            # >>> collision_wall.__dict__
            # {'name': None,
            # 'parent': <TiledMap: "resources/maps/test_pathfinding.tmx">,
            # 'visible': 1,
            # 'height': 160.0,
            # 'width': 80.0, '
            # gid': 0,
            # 'closed': False,
            # 'y': 80.0, 'x': 80.0,
            # 'rotation': 0,
            # 'type': 'collision-wall',
            # 'points': ((80.0, 80.0), (80.0, 128.0), (160.0, 128.0), (160.0, 240.0))

            # Another example:
            # 'points': ((192.0, 80.0), (192.0, 192.0))

            # For each pair of points, get the tiles on either side of the line.
            # Assumption: A pair of points will only be vertical or horizontal (no diagonal lines)

            if len(collision_line.points) < 2:
                raise Exception("Error: map has polyline with only one point")

            # get two points, and round them
            point1 = (self.round_to_divisible(collision_line.points[0][0], self.tile_size[0]),
                      self.round_to_divisible(collision_line.points[0][1], self.tile_size[1]))
            point2 = (self.round_to_divisible(collision_line.points[1][0], self.tile_size[0]),
                      self.round_to_divisible(collision_line.points[1][1], self.tile_size[1]))

            # check to see if horizontal or vertical
            line_type = None
            if point1[0] == point2[0] and point1[1] != point2[1]:
                # x's are same, must be vertical
                line_type = 'vertical'
            elif point1[0] != point2[0] and point1[1] == point2[1]:
                # y's are same, must be horizontal
                line_type = 'horizontal'
            else:
                raise Exception("Error: Points on polyline are not strictly horizontal or vertical....")

            if line_type is 'vertical':
                # get all tile coordinates on either side
                x = point1[0] / self.tile_size[0]  # same as point2[0] b/c vertical
                line_start = point1[1]
                line_end = point2[1]
                num_tiles_in_line = abs(line_start - line_end) / self.tile_size[1]  # [1] b/c vertical
                curr_y = line_start / self.tile_size[1]
                for i in range(int(num_tiles_in_line)):
                    if line_start > line_end:  # slightly different
                        # behavior depending on
                        # direction
                        left_side_tile = (x - 1, curr_y - 1)
                        right_side_tile = (x, curr_y - 1)
                        curr_y -= 1
                    else:
                        left_side_tile = (x - 1, curr_y)
                        right_side_tile = (x, curr_y)
                        curr_y += 1

                    # TODO - if we want to enable single-direction
                    # walls (i.e. for jumping) then ask map-designer
                    # to include a special property for the direction
                    # to block, and then here we only block in one
                    # direction, not both.
                    collision_lines_map.add((left_side_tile, "right"))
                    collision_lines_map.add((right_side_tile, "left"))

            elif line_type is 'horizontal':
                # get all tile coordinates on either side
                y = point1[1] / self.tile_size[1]  # same as point2[1] b/c horizontal
                line_start = point1[0]
                line_end = point2[0]
                num_tiles_in_line = abs(line_start - line_end) / self.tile_size[0]  # [0] b/c horizontal
                curr_x = line_start / self.tile_size[0]
                for i in range(int(num_tiles_in_line)):
                    if line_start > line_end:  # slightly different
                        # behavior depending on
                        # direction
                        top_side_tile = (curr_x - 1, y - 1)
                        bottom_side_tile = (curr_x - 1, y)
                        curr_x -= 1
                    else:
                        top_side_tile = (curr_x, y - 1)
                        bottom_side_tile = (curr_x, y)
                        curr_x += 1

                    # TODO - if we want to enable single-direction
                    # walls (i.e. for jumping) then ask map-designer
                    # to include a special property for the direction
                    # to block, and then here we only block in one
                    # direction, not both.
                    collision_lines_map.add((top_side_tile, "down"))
                    collision_lines_map.add((bottom_side_tile, "up"))

        return collision_map, collision_lines_map, mapsize

    @staticmethod
    def round_to_divisible(x, base=16):
        """Rounds a number to a divisible base. This is used to round collision areas that aren't
        defined well. This function assists in making sure collisions work if the map creator
        didn't set the collision areas to round numbers.

        **Examples:**

        >>> round_to_divisible(31.23, base=16)
        32
        >>> round_to_divisible(17.8, base=16)
        16

        :param x: The number we want to round.
        :param base: The base that we want our number to be divisible by. (Default: 16)

        :type x: Float
        :type base: Integer

        :rtype: Integer
        :returns: Rounded number that is divisible by "base".
        """
        return int(base * round(float(x) / base))

    @staticmethod
    def split_escaped(string_to_split, delim=","):
        """Splits a string by the specified deliminator excluding escaped
        deliminators.

        :param string_to_split: The string to split.
        :param delim: The deliminator to split the string by.

        :type string_to_split: Str
        :type delim: Str

        :rtype: List
        :returns: A list of the splitted string.

        """
        # Split by "," unless it is escaped by a "\"
        split_list = re.split(r'(?<!\\)' + delim, string_to_split)

        # Remove the escape character from the split list
        split_list = [w.replace('\,', ',') for w in split_list]

        # strip whitespace around each
        split_list = [i.strip() for i in split_list]

        return split_list

