# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import uuid
from collections.abc import Generator, Iterator
from math import cos, pi, sin
from typing import Any, Optional

import pytmx
import yaml
from natsort import natsorted

from tuxemon import prepare
from tuxemon.compat import Rect
from tuxemon.db import Direction, Orientation
from tuxemon.event import EventObject, MapAction, MapCondition
from tuxemon.graphics import scaled_image_loader
from tuxemon.lib.bresenham import bresenham
from tuxemon.map import (
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

RegionTile = tuple[
    tuple[int, int],
    Optional[RegionProperties],
]

region_properties = [
    "enter_from",
    "exit_from",
    "endure",
    "key",
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
        yaml_data: dict[str, dict[str, dict[str, Any]]] = {}

        with open(path) as fp:
            yaml_data = yaml.load(fp.read(), Loader=yaml.SafeLoader)

        for name, event_data in yaml_data["events"].items():
            _id = uuid.uuid4().int
            conds = []
            acts = []
            x = event_data.get("x", 0)
            y = event_data.get("y", 0)
            w = event_data.get("width", 1)
            h = event_data.get("height", 1)
            event_type = event_data.get("type")

            for key, value in enumerate(
                event_data.get("actions", []), start=1
            ):
                act_type, args = parse_action_string(value)
                action = MapAction(act_type, args, f"act{str(key*10)}")
                acts.append(action)
            for key, value in enumerate(
                event_data.get("conditions", []), start=1
            ):
                operator, cond_type, args = parse_condition_string(value)
                condition = MapCondition(
                    type=cond_type,
                    parameters=args,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    operator=operator,
                    name=f"cond{str(key*10)}",
                )
                conds.append(condition)
            for key, value in enumerate(event_data.get("behav", []), start=1):
                behav_type, args = parse_behav_string(value)
                _args = list(args)
                _args.insert(0, behav_type)
                _conds = MapCondition(
                    "behav", _args, x, y, w, h, "is", f"behav{str(key*10)}"
                )
                conds.insert(0, _conds)
                _squeeze = [":".join(_args)]
                _acts = MapAction("behav", _squeeze, f"behav{str(key*10)}")
                acts.insert(0, _acts)

            yield EventObject(_id, name, x, y, w, h, conds, acts)


class TMXMapLoader:
    """Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/

    """

    def __init__(self) -> None:
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
        surfable_map = list()
        collision_map: dict[tuple[int, int], Optional[RegionProperties]] = {}
        collision_lines_map = set()
        maps = data.properties

        # get all tiles which have properties and/or collisions
        gids_with_props = dict()
        gids_with_colliders = dict()
        gids_with_surfable = dict()
        for gid, props in data.tile_properties.items():
            conds = extract_region_properties(props)
            gids_with_props[gid] = conds if conds else None
            colliders = props.get("colliders")
            if colliders is not None:
                gids_with_colliders[gid] = colliders
            surfable = props.get("surfable")
            if surfable is not None:
                gids_with_surfable[gid] = surfable

        # for each tile, apply the properties and collisions for the tile location
        for layer in data.visible_tile_layers:
            layer = data.layers[layer]
            for x, y, gid in layer.iter_data():
                tile_props = gids_with_props.get(gid)
                if tile_props is not None:
                    collision_map[(x, y)] = tile_props
                # colliders
                colliders = gids_with_colliders.get(gid)
                if colliders is not None:
                    for obj in colliders:
                        obj_type = obj.type
                        if obj_type and obj_type.lower().startswith(
                            "collision"
                        ):
                            if getattr(obj, "closed", True):
                                region_conditions = copy_dict_with_keys(
                                    obj.properties, region_properties
                                )
                                _extract = extract_region_properties(
                                    region_conditions
                                )
                                collision_map[(x, y)] = _extract
                        for line in self.collision_lines_from_object(
                            obj, tile_size
                        ):
                            coords, direction = line
                            lx, ly = coords
                            line = (lx + x, ly + y), direction
                            collision_lines_map.add(line)
                # surfable
                surfable = gids_with_surfable.get(gid)
                if surfable is not None:
                    surfable_map.append((x, y))

        for obj in data.objects:
            obj_type = obj.type
            if obj_type and obj_type.lower().startswith("collision"):
                for tile_position, props in self.extract_tile_collisions(
                    obj, tile_size
                ):
                    collision_map[tile_position] = props
                for line in self.collision_lines_from_object(obj, tile_size):
                    collision_lines_map.add(line)
            elif obj_type and obj_type.lower().startswith("surfable"):
                surfable_map.append(tile_size)
            elif obj_type == "event":
                events.append(self.load_event(obj, tile_size))
            elif obj_type == "init":
                inits.append(self.load_event(obj, tile_size))

        return TuxemonMap(
            events,
            inits,
            surfable_map,
            collision_map,
            collision_lines_map,
            data,
            maps,
            filename,
        )

    def extract_tile_collisions(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[RegionTile, None, None]:
        if getattr(tiled_object, "closed", True):
            yield from self.region_tiles(tiled_object, tile_size)

    def collision_lines_from_object(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[tuple[tuple[int, int], Direction], None, None]:
        # TODO: test dropping "collision_lines_map" and replacing with "enter/exit" tiles
        if not getattr(tiled_object, "closed", True):
            for item in self.process_line(tiled_object, tile_size):
                blocker0, blocker1, orientation = item
                if orientation == Orientation.vertical:
                    yield blocker0, Direction.left
                    yield blocker1, Direction.right
                elif orientation == Orientation.horizontal:
                    yield blocker1, Direction.down
                    yield blocker0, Direction.up
                else:
                    raise Exception(orientation)

    def process_line(
        self,
        line: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[
        tuple[tuple[int, int], tuple[int, int], Orientation], None, None
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
        grid_size: tuple[int, int],
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
        tile_size: tuple[int, int],
    ) -> EventObject:
        """
        Load an Event from the map.

        Parameters:
            obj: Tiled object that represents an event.
            tile_size: Size of a tile.

        Returns:
            Loaded event.

        """
        _id = uuid.uuid4().int
        conds = []
        acts = []
        x = int(obj.x / tile_size[0])
        y = int(obj.y / tile_size[1])
        w = int(obj.width / tile_size[0])
        h = int(obj.height / tile_size[1])

        properties = obj.properties
        keys = natsorted(properties.keys())
        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on...
        for key in keys:
            if not isinstance(key, str):
                continue
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
            if not isinstance(key, str):
                continue
            if key.startswith("behav"):
                behav_string = properties[key]
                behav_type, args = parse_behav_string(behav_string)
                _args = list(args)
                _args.insert(0, behav_type)
                conds.insert(
                    0,
                    MapCondition("behav", _args, x, y, w, h, "is", key),
                )
                _squeeze = [":".join(_args)]
                acts.insert(0, MapAction("behav", _squeeze, key))

        return EventObject(_id, obj.name, x, y, w, h, conds, acts)
