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
from math import cos, sin, pi

import pytmx

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core.graphics import scaled_image_loader
from tuxemon.core.map import (
    TuxemonMap,
    tiles_inside_rect,
    snap_rect,
    point_to_grid,
    angle_of_points,
    orientation_by_angle,
    extract_region_properties,
)
from tuxemon.core.script.parser import Parser
from tuxemon.core.tools import copy_dict_with_keys
from tuxemon.lib.bresenham import bresenham

logger = logging.getLogger(__name__)

# TODO: standardize and document these values
region_properties = [
    "enter",
    "enter_from",
    "enter_to",
    "exit",
    "exit_from",
    "exit_to",
    "continue",
]


class TMXMapLoader:
    """ Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/

    """

    def load(self, filename):
        """ Load map data from a tmx map file

        Loading the map data is done using the pytmx library.

        Specifications for the TMX map format can be found here:
        https://github.com/bjorn/tiled/wiki/TMX-Map-Format

        The list of tiles is structured in a way where you can access an
        individual tile by index number.

        The collision map is a set of (x,y) coordinates that the player cannot
        walk through. This set is generated based on collision regions defined
        in the map file.

        **Examples:**

        In each map, there are three types of objects: **collisions**,
        **conditions**, and *actions**. Here is how an action would be defined
        using the Tiled map editor:

        .. image:: images/map/map_editor_action01.png

        :param filename: The path to the tmx map file to load.
        :type filename: String

        :rtype: tuxemon.core.map.TuxemonMap
        """
        parser = Parser()
        data = pytmx.TiledMap(
            filename, image_loader=scaled_image_loader, pixelalpha=True
        )
        tile_size = (data.tilewidth, data.tileheight)
        data.tilewidth, data.tileheight = prepare.TILE_SIZE
        events = list()
        inits = list()
        interacts = list()
        collision_map = dict()
        collision_lines_map = set()
        edges = data.properties.get("edges")

        for obj in data.objects:
            if obj.type and obj.type.lower().startswith("collision"):
                closed = getattr(obj, "closed", True)
                if closed:
                    # closed; polygon or region with bounding box
                    for tile_position, conds in self.region_tiles(obj, tile_size):
                        collision_map[tile_position] = conds if conds else None
                else:
                    # not closed; a line of one ore more segments
                    for item in self.process_line(obj, tile_size):
                        # TODO: test dropping "collision_lines_map" and replacing with "enter/exit" tiles
                        i, m, orientation = item
                        if orientation == "vertical":
                            collision_lines_map.add((i, "left"))
                            collision_lines_map.add((m, "right"))
                        elif orientation == "horizontal":
                            collision_lines_map.add((m, "down"))
                            collision_lines_map.add((i, "up"))
                        else:
                            raise Exception(orientation)
            elif obj.type == "event":
                events.append(self.load_event(obj, tile_size))
            elif obj.type == "init":
                inits.append(self.load_event(obj, tile_size))
            elif obj.type == "interact":
                interacts.append(self.load_event(obj, tile_size))

        return TuxemonMap(
            events,
            inits,
            interacts,
            collision_map,
            collision_lines_map,
            data,
            edges,
            filename,
        )

    @staticmethod
    def process_line(line, tile_size):
        """ Identify the tiles on either side of the line and block movement along it

        :param line:
        :param tile_size:
        :return:
        """
        if len(line.points) < 2:
            raise ValueError("Error: collision lines must be at least 2 points")
        for point_0, point_1 in zip(line.points, line.points[1:]):
            p0 = point_to_grid(point_0, tile_size)
            p1 = point_to_grid(point_1, tile_size)
            p0, p1 = sorted((p0, p1))
            angle = angle_of_points(p0, p1)
            orientation = orientation_by_angle(angle)
            for i in bresenham(p0[0], p0[1], p1[0], p1[1], include_end=False):
                angle1 = angle - (pi / 2)
                other = int(round(cos(angle1) + i[0])), int(round(sin(angle1) + i[1]))
                yield i, other, orientation

    @staticmethod
    def region_tiles(region, grid_size):
        """ Apply region properties to individual tiles

        Right now our collisions are defined in our tmx file as large regions
        that the player can't pass through. We need to convert these areas
        into individual tile coordinates that the player can't pass through.
        Loop through all of the collision objects in our tmx file. The
        region's bounding box will be snapped to the nearest tile coordinates.

        :param region:
        :param grid_size:
        :return:
        """
        region_conditions = copy_dict_with_keys(region.properties, region_properties)
        rect = snap_rect(
            Rect(region.x, region.y, region.width, region.height), grid_size
        )
        for tile_position in tiles_inside_rect(rect, grid_size):
            yield tile_position, extract_region_properties(region_conditions)
