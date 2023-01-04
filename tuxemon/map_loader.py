# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from math import cos, pi, sin
from typing import Any, Dict, Generator, Iterator, Mapping, Optional, Tuple

import pytmx
import yaml
from natsort import natsorted

from tuxemon import prepare
from tuxemon.compat import Rect
from tuxemon.event import EventObject, MapAction, MapCondition
from tuxemon.graphics import scaled_image_loader
from tuxemon.lib.bresenham import bresenham
from tuxemon.map import (
    Direction,
    Orientation,
    RegionProperties,
    TuxemonMap,
    angle_of_points,
    extract_region_properties,
    orientation_by_angle,
    point_to_grid,
    snap_rect,
    tiles_inside_rect,
)
from tuxemon.script.parser import (
    parse_action_string,
    parse_behav_string,
    parse_condition_string,
)
from tuxemon.tools import copy_dict_with_keys

logger = logging.getLogger(__name__)

RegionTile = Tuple[
    Tuple[int, int],
    Optional[Mapping[str, Any]],
]

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


class YAMLEventLoader:
    """
    Support for reading game events from a YAML file.
    """

    def load_events(self, path: str) -> Iterator[EventObject]:
        """
        Load EventObjects from YAML file.

        Parameters:
            path: Path to the file.

        """
        with open(path) as fp:
            yaml_data = yaml.load(fp.read(), Loader=yaml.SafeLoader)

        for name, event_data in yaml_data["events"].items():
            conds = []
            acts = []
            x = event_data.get("x")
            y = event_data.get("y")
            w = event_data.get("width")
            h = event_data.get("height")
            event_type = event_data.get("type")

            for value in event_data.get("actions", []):
                act_type, args = parse_action_string(value)
                action = MapAction(act_type, args, None)
                acts.append(action)
            for value in event_data.get("conditions", []):
                operator, cond_type, args = parse_condition_string(value)
                condition = MapCondition(
                    type=cond_type,
                    parameters=args,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    operator=operator,
                    name="",
                )
                conds.append(condition)
            for value in event_data.get("behav", []):
                behav_type, args = parse_behav_string(value)
                if behav_type == "talk":
                    condition = MapCondition(
                        type="to_talk",
                        parameters=args,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        operator="is",
                        name="",
                    )
                    conds.insert(0, condition)
                    action = MapAction(
                        type="npc_face",
                        parameters=[args[0], "player"],
                        name="",
                    )
                    acts.insert(0, action)
                else:
                    raise Exception
            if event_type == "interact":
                cond_data = MapCondition(
                    "player_facing_tile",
                    list(),
                    x,
                    y,
                    w,
                    h,
                    "is",
                    None,
                )
                conds.append(cond_data)

            yield EventObject(name, name, x, y, w, h, conds, acts)


class TMXMapLoader:
    """Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/

    """

    def __init__(self):
        # Makes mocking easier during tests
        self.image_loader = scaled_image_loader

    def load(self, filename: str) -> TuxemonMap:
        """Load map data from a tmx map file.

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

        Parameters:
            filename: The path to the tmx map file to load.

        Returns:
            The loaded map.

        """
        data = pytmx.TiledMap(
            filename=filename,
            image_loader=self.image_loader,
            pixelalpha=True,
        )
        tile_size = (data.tilewidth, data.tileheight)
        data.tilewidth, data.tileheight = prepare.TILE_SIZE
        events = list()
        inits = list()
        interacts = list()
        collision_map: Dict[Tuple[int, int], Optional[RegionProperties]] = {}
        collision_lines_map = set()
        maps = data.properties

        # get all tiles which have properties and/or collisions
        gids_with_props = dict()
        gids_with_colliders = dict()
        for gid, props in data.tile_properties.items():
            conds = extract_region_properties(props)
            gids_with_props[gid] = conds if conds else None
            colliders = props.get("colliders")
            if colliders is not None:
                gids_with_colliders[gid] = colliders

        # for each tile, apply the properties and collisions for the tile location
        for layer in data.visible_tile_layers:
            layer = data.layers[layer]
            for x, y, gid in layer.iter_data():
                tile_props = gids_with_props.get(gid)
                if tile_props is not None:
                    collision_map[(x, y)] = tile_props
                colliders = gids_with_colliders.get(gid)
                if colliders is not None:
                    for obj in colliders:
                        if obj.type and obj.type.lower().startswith(
                            "collision"
                        ):
                            if getattr(obj, "closed", True):
                                region_conditions = copy_dict_with_keys(
                                    obj.properties, region_properties
                                )
                                collision_map[(x, y)] = region_conditions
                        for line in self.collision_lines_from_object(
                            obj, tile_size
                        ):
                            coords, direction = line
                            lx, ly = coords
                            line = (lx + x, ly + y), direction
                            collision_lines_map.add(line)

        for obj in data.objects:
            if obj.type and obj.type.lower().startswith("collision"):
                for tile_position, props in self.extract_tile_collisions(
                    obj, tile_size
                ):
                    collision_map[tile_position] = props
                for line in self.collision_lines_from_object(obj, tile_size):
                    collision_lines_map.add(line)
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
            maps,
            filename,
        )

    def extract_tile_collisions(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: Tuple[int, int],
    ) -> Generator[RegionTile, None, None]:
        if getattr(tiled_object, "closed", True):
            yield from self.region_tiles(tiled_object, tile_size)

    def collision_lines_from_object(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: Tuple[int, int],
    ) -> Generator[Tuple[Tuple[int, int], Direction], None, None]:
        # TODO: test dropping "collision_lines_map" and replacing with "enter/exit" tiles
        if not getattr(tiled_object, "closed", True):
            for item in self.process_line(tiled_object, tile_size):
                blocker0, blocker1, orientation = item
                if orientation == "vertical":
                    yield blocker0, "left"
                    yield blocker1, "right"
                elif orientation == "horizontal":
                    yield blocker1, "down"
                    yield blocker0, "up"
                else:
                    raise Exception(orientation)

    def process_line(
        self,
        line: pytmx.TiledObject,
        tile_size: Tuple[int, int],
    ) -> Generator[
        Tuple[Tuple[int, int], Tuple[int, int], Orientation], None, None
    ]:
        """Identify the tiles on either side of the line and block movement along it."""
        if len(line.points) < 2:
            raise ValueError(
                "Error: collision lines must be at least 2 points"
            )
        for point_0, point_1 in zip(line.points, line.points[1:]):
            p0 = point_to_grid(point_0, tile_size)
            p1 = point_to_grid(point_1, tile_size)
            p0, p1 = sorted((p0, p1))
            angle = angle_of_points(p0, p1)
            orientation = orientation_by_angle(angle)
            for i in bresenham(p0[0], p0[1], p1[0], p1[1], include_end=False):
                angle1 = angle - (pi / 2)
                other = int(round(cos(angle1) + i[0])), int(
                    round(sin(angle1) + i[1])
                )
                yield i, other, orientation

    @staticmethod
    def region_tiles(
        region: pytmx.TiledObject,
        grid_size: Tuple[int, int],
    ) -> Generator[RegionTile, None, None]:
        """
        Apply region properties to individual tiles.

        Right now our collisions are defined in our tmx file as large regions
        that the player can't pass through. We need to convert these areas
        into individual tile coordinates that the player can't pass through.
        Loop through all of the collision objects in our tmx file. The
        region's bounding box will be snapped to the nearest tile coordinates.

        Parameters:
            region: The Tiled object which contains collisions and movement
                modifiers.
            grid_size: The tile grid size.

        Yields:
            Tuples with form (tile position, properties).
        """
        region_conditions = copy_dict_with_keys(
            region.properties,
            region_properties,
        )
        rect = snap_rect(
            Rect((region.x, region.y, region.width, region.height)),
            grid_size,
        )
        for tile_position in tiles_inside_rect(rect, grid_size):
            yield tile_position, extract_region_properties(region_conditions)

    def load_event(
        self,
        obj: pytmx.TiledObject,
        tile_size: Tuple[int, int],
    ) -> EventObject:
        """
        Load an Event from the map.

        Parameters:
            obj: Tiled object that represents an event.
            tile_size: Size of a tile.

        Returns:
            Loaded event.

        """
        conds = []
        acts = []
        x = int(obj.x / tile_size[0])
        y = int(obj.y / tile_size[1])
        w = int(obj.width / tile_size[0])
        h = int(obj.height / tile_size[1])

        properties = obj.properties
        keys = natsorted(properties.keys())
        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on..
        for key in keys:
            value = properties[key]
            if key.startswith("cond"):
                operator, cond_type, args = parse_condition_string(value)
                condition = MapCondition(
                    cond_type, args, x, y, w, h, operator, key
                )
                conds.append(condition)
            elif key.startswith("act"):
                act_type, args = parse_action_string(value)
                action = MapAction(act_type, args, key)
                acts.append(action)

        for key in keys:
            if key.startswith("behav"):
                behav_string = properties[key]
                behav_type, args = parse_behav_string(behav_string)
                if behav_type == "talk":
                    conds.insert(
                        0, MapCondition("to_talk", args, x, y, w, h, "is", key)
                    )
                    acts.insert(
                        0, MapAction("npc_face", [args[0], "player"], key)
                    )
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
