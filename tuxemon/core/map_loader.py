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
    snap_rect_to_grid,
    snap_rect_to_tile,
    angle_of_points,
    orientation_by_angle,
    snap_to_grid,
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


def event_actions_and_conditions(items):
    """ Return list of acts and conditions from a list of items

    :param Rect rect: Area for the event
    :param Iterator[Tuple[str, str]] items: List of [name, value] tuples
    :rtype: Tuple[List, List]
    """
    conds = []
    acts = []

    # We need to sort them by name, so that "act1" comes before "act2" and so on...
    for key, value in natsorted(items):
        if key.startswith("cond"):
            operator, cond_type, args = parse_condition_string(value)
            condition = MapCondition(cond_type, operator, args)
            conds.append(condition)
        elif key.startswith("act"):
            act_type, args = parse_action_string(value)
            action = MapAction(act_type, args)
            acts.append(action)
        elif key.startswith("behav"):
            behav_type, args = parse_behav_string(value)
            if behav_type == "talk":
                cond = MapCondition("to_talk", "is", args)
                action = MapAction("npc_face", [args[0], "player"])
                conds.insert(0, cond)
                acts.insert(0, action)
            else:
                raise ValueError("Bad event parameter: {}".format(key))
        else:
            raise ValueError("Bad event parameter: {}".format(key))

    return acts, conds


def new_event_object(event_id, name, event_type, rect, properties):
    """

    :param str event_id: Unique ID of the event
    :param str name: Name of the Event
    :param str event_type: Special purpose
    :param Rect rect: Area of map where event is triggered; must be in tile coords
    :param Iterable properties: Iterable of Tuple[key, value] (like Dict.items())
    :rtype: EventObject
    """
    acts, conds = event_actions_and_conditions(properties)
    if event_type == "interact":
        cond = MapCondition("player_facing_tile", "is", None)
        conds.append(cond)
    return EventObject(event_id, name, rect, conds, acts)


class TMXMapLoader(object):
    """ Load map from standard tmx files created by Tiled.

    Events and collision regions are loaded and put in the appropriate data
    structures for the game to understand.

    **Tiled:** http://www.mapeditor.org/

    """

    def load(self, filename):
        """ Load map data from a tmx map file

        Loading the map data is done using the pytmx library.

        Specifications for the TMX map format can be found here:
        https://github.com/bjorn/tiled/wiki/TMX-Map-Format

        The list of tiles is structured in a way where you can access an
        individual tile by index number.

        Tile images and other graphical data should not be loaded here.

        The collision map is a set of (x,y) coordinates that the player cannot
        walk through. This set is generated based on collision regions defined
        in the map file.

        **Examples:**

        In each map, there are three types of objects: **collisions**,
        **conditions**, and *actions**. Here is how an action would be defined
        using the Tiled map editor:

        .. image:: images/map/map_editor_action01.png

        :param str filename: The path to the tmx map file to load.
        :rtype: tuxemon.core.map.TuxemonMap
        """
        # TODO: remove the need to load graphics here
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
            p0 = snap_to_grid(point_0, tile_size)
            p1 = snap_to_grid(point_1, tile_size)
            p0, p1 = sorted((p0, p1))
            angle = angle_of_points(p0, p1)
            orientation = orientation_by_angle(angle)
            for i in bresenham(p0[0], p0[1], p1[0], p1[1], include_end=False):
                angle1 = angle - (pi / 2)
                other = int(round(cos(angle1) + i[0])), int(round(sin(angle1) + i[1]))
                yield i, other, orientation

    def region_tiles(self, region, grid_size):
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
        rect = snap_rect_to_grid(self.rect_from_object(region), grid_size)
        for tile_position in tiles_inside_rect(rect, grid_size):
            yield tile_position, self.extract_region_properties(region_conditions)

    def load_event(self, tiled_object, tile_size):
        """ Return MapEvent for the tiled object

        :param tiled_object:
        :param tile_size:
        :return:
        """
        return new_event_object(
            tiled_object.id,
            tiled_object.name,
            tiled_object.type,
            snap_rect_to_tile(self.rect_from_object(tiled_object), tile_size),
            tiled_object.properties.items(),
        )

    @staticmethod
    def extract_region_properties(region):
        """ Return Dict of data we need, ignoring what we don't

        :param Dict region:
        :rtype:  Dict
        """
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

    @staticmethod
    def rect_from_object(obj):
        """ Return Rect from TiledObject

        :param obj: TiledObject
        :rtype: Rect
        """
        return Rect(obj.x, obj.y, obj.width, obj.height)
