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
from natsort import natsorted

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core.event import EventObject, MapAction, MapCondition
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
from tuxemon.core.tools import split_escaped, copy_dict_with_keys
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


def parse_action_string(text):
    words = text.split(" ", 1)
    act_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return act_type, args


def parse_condition_string(text):
    words = text.split(" ", 2)
    operator, cond_type = words[0:2]
    if len(words) > 2:
        args = split_escaped(words[2])
    else:
        args = list()
    return operator, cond_type, args


def parse_behav_string(behav_string):
    words = behav_string.split(" ", 1)
    behav_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return behav_type, args


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

    def process_line(self, line, tile_size):
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

    def load_event(self, obj, tile_size):
        """ Load an Event from the map

        :param obj:
        :param tile_size:
        :rtype: EventObject
        """
        conds = []
        acts = []
        x = int(obj.x / tile_size[0])
        y = int(obj.y / tile_size[1])
        w = int(obj.width / tile_size[0])
        h = int(obj.height / tile_size[1])

        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on..
        for key, value in natsorted(obj.properties.items()):
            if key.startswith("cond"):
                operator, cond_type, args = parse_condition_string(value)
                condition = MapCondition(cond_type, args, x, y, w, h, operator, key)
                conds.append(condition)
            elif key.startswith("act"):
                act_type, args = parse_action_string(value)
                action = MapAction(act_type, args, key)
                acts.append(action)

        keys = natsorted(obj.properties.keys())
        for key in keys:
            if key.startswith("behav"):
                behav_string = obj.properties[key]
                behav_type, args = parse_behav_string(behav_string)
                if behav_type == "talk":
                    conds.insert(
                        0, MapCondition("to_talk", args, x, y, w, h, "is", key)
                    )
                    acts.insert(0, MapAction("npc_face", [args[0], "player"], key))
                else:
                    raise Exception

        # add a player_facing_tile condition automatically
        if obj.type == "interact":
            cond_data = MapCondition(
                "player_facing_tile", list(), x, y, w, h, "is", None
            )
            logger.debug(cond_data)
            conds.append(cond_data)

        return EventObject(obj.id, obj.name, x, y, w, h, conds, acts)
