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
from typing import Tuple, Iterator, Dict, List

import pytmx
import yaml

from tuxemon import prepare
from tuxemon.compat import Rect
from tuxemon.event import EventObject, MapAction, MapCondition
from tuxemon.graphics import scaled_image_loader
from tuxemon.lib.bresenham import bresenham
from tuxemon.map import (
    TuxemonMap,
    angle_of_points,
    orientation_by_angle,
    region_properties,
    snap_rect_to_grid,
    snap_rect_to_tile,
    snap_to_grid,
    tiles_inside_rect,
)
from tuxemon.script.oldparser import (
    event_actions_and_conditions,
    parse_action_string,
    parse_condition_string,
    parse_behav_string,
    process_behav_string,
    process_condition_string,
    process_action_string,
)
from tuxemon.tools import copy_dict_with_keys, maybe_get_as_type

logger = logging.getLogger(__name__)


def new_event_object(
    event_id: str, name: str, event_type: str, rect: Rect, properties: List
) -> EventObject:
    """
    Return a new EventObject

    Parameters:
        event_id: Unique ID of the event
        name: Name of the Event
        event_type: Special purpose
        rect: Area of map where event is triggered; must be in tile coords
        properties: Iterable of Tuple[key, value] (like Dict.items())
    """
    acts, conds = event_actions_and_conditions(properties)
    if event_type == "interact":
        cond = MapCondition("player_facing_tile", "is", None)
        conds.append(cond)
    return EventObject(event_id, name, rect, conds, acts)


class YAMLEventLoader:
    """
    Support for reading game events from a YAML file
    """

    def load_events(self, path: str) -> Iterator[EventObject]:
        """
        Load EventObjects from YAML file

        Parameters:
            path: Path to the file
        """
        with open(path) as fp:
            yaml_data = yaml.load(fp.read(), Loader=yaml.SafeLoader)

        for name, event_data in yaml_data["events"].items():
            conds = []
            acts = []
            rect = self.rect_from_event(event_data)

            for section, func in (
                ("actions", process_action_string),
                ("conditions", process_condition_string),
                ("behav", process_behav_string),
            ):
                for value in event_data.get(section, []):
                    _conds, _acts = func(value)
                    conds.extend(_conds)
                    acts.extend(_acts)

            yield EventObject(None, name, rect, conds, acts)

    def rect_from_event(self, event_data: Dict):
        x = maybe_get_as_type("x", event_data, int)
        y = maybe_get_as_type("y", event_data, int)
        w = maybe_get_as_type("width", event_data, int)
        h = maybe_get_as_type("height", event_data, int)

        # TODO: better handling
        if all(isinstance(i, int) for i in (x, y, w, h)):
            return Rect(x, y, w, h)
        else:
            raise ValueError


class TMXMapLoader:
    """Load map from standard tmx files created by Tiled."""

    def load(self, filepath: str) -> TuxemonMap:
        """
        Load map data from a tmx map file

        Loading the map data is done using the pytmx library.
        """
        # TODO: remove the need to load graphics here
        data = pytmx.TiledMap(
            filepath, image_loader=scaled_image_loader, pixelalpha=True
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
            filepath,
        )

    def process_line(self, line, tile_size: Tuple[int, int]):
        """Identify the tiles on either side of the line and block movement along it

        Parameters:
            line: pytmx TiledLine object
            tile_size:
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

    def region_tiles(self, region, grid_size: Tuple[int, int]):
        """
        Apply region properties to individual tiles

        Right now our collisions are defined in our tmx file as large regions
        that the player can't pass through. We need to convert these areas
        into individual tile coordinates that the player can't pass through.
        Loop through all of the collision objects in our tmx file. The
        region's bounding box will be snapped to the nearest tile coordinates.

        Parameters:
            region: pytmx TiledObject
            grid_size:
        """
        region_conditions = copy_dict_with_keys(region.properties, region_properties)
        rect = snap_rect_to_grid(self.rect_from_object(region), grid_size)
        for tile_position in tiles_inside_rect(rect, grid_size):
            yield tile_position, self.extract_region_properties(region_conditions)

    def load_event(self, tiled_object, tile_size):
        """Return MapEvent for the tiled object

        :param tiled_object:
        :param tile_size:
        """
        return new_event_object(
            tiled_object.id,
            tiled_object.name,
            tiled_object.type,
            snap_rect_to_tile(self.rect_from_object(tiled_object), tile_size),
            tiled_object.properties.items(),
        )

    @staticmethod
    def extract_region_properties(region) -> Dict:
        """
        Return Dict of data we need, ignoring what we don't
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
    def rect_from_object(obj) -> Rect:
        """
        Return Rect from TiledObject

        """
        return Rect(obj.x, obj.y, obj.width, obj.height)
