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
# core.components.map Game map module.
#
#
from __future__ import absolute_import
from __future__ import division

import logging
import re

from core import prepare, tools
from core.components.event import MapAction
from core.components.event import MapCondition
from core.components.event import EventObject

import pytmx
from pytmx.util_pygame import handle_transformation, smart_convert, load_pygame
import pyscroll

import pygame

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


def scaled_image_loader(filename, colorkey, **kwargs):
    """ pytmx image loader for pygame

    Modified to load images at a scaled size

    :param filename:
    :param colorkey:
    :param kwargs:
    :return:
    """
    if colorkey:
        colorkey = pygame.Color('#{0}'.format(colorkey))

    pixelalpha = kwargs.get('pixelalpha', True)

    # load the tileset image
    image = pygame.image.load(filename)

    # scale the tileset image to match game scale
    scaled_size = tools.scale_sequence(image.get_size())
    image = pygame.transform.scale(image, scaled_size)

    def load_image(rect=None, flags=None):
        if rect:
            # scale the rect to match the scaled image
            rect = tools.scale_rect(rect)
            try:
                tile = image.subsurface(rect)
            except ValueError:
                logger.error('Tile bounds outside bounds of tileset image')
                raise
        else:
            tile = image.copy()

        if flags:
            tile = handle_transformation(tile, flags)

        tile = smart_convert(tile, colorkey, pixelalpha)
        return tile

    return load_image


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

        # Get the tile size from a tileset in our map. This is used to calculate the number of tiles
        # in a collision region.
        self.tile_size = (0, 0)

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

        :param filename: The path to the tmx map file to load.

        :type filename: String

        :rtype: None
        :returns: None

        **Examples:**

        In each map, there are three types of objects: **collisions**, **conditions**, and
        **actions**. Here is how an action would be defined using the Tiled map editor:

        .. image:: images/map/map_editor_action01.png

        Here is an example of how we use pytmx to load the map data from a tmx file and what
        those objects would look like after loading:

        >>> tmx_data = pytmx.TiledMap("pallet_town-room.tmx")
        >>> for obj in tmx_data.objects:
        ...     pprint.pprint(obj.__dict__)
        ...
        {'gid': 0,
         'height': 32,
         'name': None,
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'rotation': 0,
         'type': 'collision',
         'visible': 1,
         'width': 16,
         'x': 160,
         'y': 48}
        {'action_id': '9',
         'condition_type': 'player_at',
         'gid': 0,
         'height': 16,
         'id': 9,
         'name': 'Start Combat',
         'operator': 'is',
         'parameters': '1,11',
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'rotation': 0,
         'type': 'condition',
         'visible': 1,
         'width': 16,
         'x': 16,
         'y': 176}
        {'action_type': 'teleport',
         'gid': 0,
         'height': 16,
         'id': 5,
         'name': 'Go Downstairs',
         'parameters': 'test.tmx,5,5',
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'priority': '1',
         'rotation': 0,
         'type': 'action',
         'visible': 1,
         'width': 16,
         'x': 0,
         'y': 0}

        """
        # Load the tmx map data using the pytmx library.
        self.filename = filename

        # Scale the loaded tiles if enabled
        if prepare.CONFIG.scaling == "1":
            self.data = pytmx.TiledMap(filename,
                                       image_loader=scaled_image_loader,
                                       pixelalpha=True)
            self.data.tilewidth, self.data.tileheight = prepare.TILE_SIZE
        else:
            self.data = load_pygame(filename, pixelalpha=True)

        # make a scrolling renderer
        self.renderer = self.initialize_renderer()

        # Get the map dimensions
        self.size = self.data.width, self.data.height

        # Get the tile size of the map
        self.tile_size = self.data.tilesets[0].tilewidth, self.data.tilesets[0].tileheight

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
        visual_data = pyscroll.data.TiledMapData(self.data)
        # TODO: Tuxemon will not work with clamp_camera=True
        return pyscroll.BufferedRenderer(visual_data, prepare.SCREEN_SIZE, clamp_camera=False)

    def loadevent(self, obj):
        conds = []
        acts = []

        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on..
        keys = sorted(obj.properties.keys())

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
                condition = MapCondition(cond_type, args, x, y, w, h, operator)
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
                action = MapAction(act_type, args)
                acts.append(action)

        # TODO: move this to some post-creation function, as more may be needed
        # add a player_facing_tile condition automatically
        if obj.type == "interact":
            cond_data = MapCondition("player_facing_tile", list(), x, y, w, h, "is")
            logger.debug(cond_data)
            conds.append(cond_data)

        return EventObject(obj.id, x, y, conds, acts)

    def loadfile(self, tile_size):
        """Loads the tile and collision data from the map file and returns a list of tiles with
        their position and pygame surface, a set of collision tile coordinates, and the size of
        the map itself. The list of tile surfaces is used to draw the map in the main game. The
        list of collision tile coordinates is used for collision detection.

        :param tile_size: An [x, y] size of each tile in pixels AFTER scaling. This is used for
            scaling and positioning.

        :type tile_size: List

        :rtype: List
        :returns: A multi-dimensional list of tiles in dictionary format; a set of collision
            coordinates; the map size.

        **Examples:**

        The list of tiles is structured in a way where you can access an individual tile by
        index number. For example, to get a tile located at (2, 1), you can access the tile's
        details using:

        >>> x = 2
        >>> y = 1
        >>> layer = 0
        >>> tiles[x][y][layer]

        Here is an example of what the the tiles list data structure actually looks like:

        >>> tiles, collisions, mapsize =  map.loadfile([24, 24])
        >>> tiles
            [
              [
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                []
              ],
              [ [],
                [{'layer': 1,
                'name': '6,0',
                'position': (80, 80),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 1],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '7,0',
                'position': (80, 160),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 2],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '8,0',
                'position': (80, 240),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 3],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '9,0',
                'position': (80, 320),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 4],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '9,0',
                'position': (80, 400),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 5],
                'tileset': 'resources/gfx/tileset.png'},
                {'layer': 3,
                'name': '10,0',
                'position': (80, 400),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 5],
                'tileset': 'resources/gfx/tileset.png'}],
        ...


        The collision map is a set of (x,y) coordinates that the player cannot walk
        through. This set is generated based on collision regions defined in the
        map file.

        Here is an example of what the collision set looks like:

        >>> tiles, collisions, mapsize =  map.loadfile([24, 24])
        >>> collisions
        set([(0, 2),
             (0, 3),
             (0, 4),
             (0, 5),
             (0, 6)])

        """
        # Get the dimensions of the map
        mapsize = self.size

        # Create a list of all tile monsters_in_play that we cannot walk through
        collision_map = {}

        # Create a dictionary of coordinates that have conditional collisions
        cond_collision_map = {}

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
                    collision_map[collision_tile] = "None"

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

        :param x: The number we want to round.
        :param base: The base that we want our number to be divisible by. (Default: 16)

        :type x: Float
        :type base: Integer

        :rtype: Integer
        :returns: Rounded number that is divisible by "base".

        **Examples:**

        >>> round_to_divisible(31.23, base=16)
        32
        >>> round_to_divisible(17.8, base=16)
        16

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

        return split_list


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
