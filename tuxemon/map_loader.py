# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import uuid
from collections import defaultdict
from collections.abc import Generator, MutableMapping
from math import cos, pi, sin
from pathlib import Path
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


def parse_yaml(path: str) -> Any:
    """
    Parses a large YAML file efficiently using a streaming loader.
    """
    with open(path) as fp:
        try:
            return yaml.load(fp.read(), Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")


class EventLoader:
    """
    Handles loading collision and specific events from YAML files.
    """

    def __init__(self) -> None:
        self.yaml_loader = YAMLEventLoader()

    def load_collision_events(
        self, yaml_file: Path
    ) -> MutableMapping[tuple[int, int], Optional[RegionProperties]]:
        """
        Loads collision event data from a YAML file.

        Parameters:
            yaml_file: The path to the YAML file.

        Returns:
            A dictionary mapping coordinates to collision properties.
        """
        try:
            return self.yaml_loader.load_collision(yaml_file.as_posix())
        except Exception as e:
            logger.error(
                f"Failed to load collision events from {yaml_file}: {e}"
            )
            return {}

    def load_specific_events(
        self, yaml_file: Path, event_type: str
    ) -> list[EventObject]:
        """
        Loads specific events (e.g., 'event' or 'init') from a YAML file.

        Parameters:
            yaml_file: The path to the YAML file.
            event_type: The type of event to load.

        Returns:
            A list of events of the specified type.
        """
        try:
            return self.yaml_loader.load_events(
                yaml_file.as_posix(), event_type
            )[event_type]
        except Exception as e:
            logger.error(
                f"Failed to load '{event_type}' events from {yaml_file}: {e}"
            )
            return []


class MapLoader:
    def __init__(self) -> None:
        self.event_loader = EventLoader()

    def load_map_data(self, path: str) -> TuxemonMap:
        """
        Loads map data from a TMX file and associated YAML event files.

        Parameters:
            path: The path to the TMX map file.

        Returns:
            A TuxemonMap object containing the loaded map data and events.
        """
        logger.debug(f"Load map '{path}'.")
        txmn_map = self._load_map_from_disk(path)
        self._process_and_merge_events(txmn_map, path)
        return txmn_map

    def _load_map_from_disk(self, path: str) -> TuxemonMap:
        """
        Loads only the TMX map data from the file.

        Parameters:
            path: The path to the TMX map file.

        Returns:
            A TuxemonMap object with the loaded map data.
        """
        try:
            return TMXMapLoader().load(path)
        except Exception as e:
            logger.error(f"Failed to load TMX map from {path}: {e}")
            raise

    def _process_events(self, yaml_files: list[Path]) -> tuple[
        MutableMapping[tuple[int, int], Optional[RegionProperties]],
        defaultdict[str, list[EventObject]],
    ]:
        """
        Processes events from YAML files and returns structured data.

        Parameters:
            yaml_files: List of YAML file paths.

        Returns:
            Tuple containing collision map and event dictionary.
        """
        yaml_collision: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ] = {}
        events: defaultdict[str, list[EventObject]] = defaultdict(list)

        for yaml_file in yaml_files:
            if yaml_file.exists():
                yaml_collision.update(
                    self.event_loader.load_collision_events(yaml_file)
                )
                events["event"].extend(
                    self.event_loader.load_specific_events(yaml_file, "event")
                )
                events["init"].extend(
                    self.event_loader.load_specific_events(yaml_file, "init")
                )
            else:
                logger.warning(f"YAML file {yaml_file} not found")

        return yaml_collision, events

    def _merge_events(
        self,
        txmn_map: TuxemonMap,
        yaml_collision: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ],
        events: dict[str, list[EventObject]],
    ) -> None:
        """
        Merges processed events into the TuxemonMap.

        Parameters:
            txmn_map: The TuxemonMap object to update.
            yaml_collision: Collision event data.
            events: Dictionary containing events and init sequences.
        """
        # Debugging before merging
        logger.debug(f"TMX events before merging: {len(txmn_map.events)}")
        logger.debug(f"TMX inits before merging: {len(txmn_map.inits)}")

        txmn_map.collision_map.update(yaml_collision)
        txmn_map.events = list(txmn_map.events) + events["event"]
        txmn_map.inits = list(txmn_map.inits) + events["init"]

        # Debugging after merging
        logger.debug(f"Total TMX events after merge: {len(txmn_map.events)}")
        logger.debug(f"Total TMX inits after merge: {len(txmn_map.inits)}")

    def _process_and_merge_events(
        self, txmn_map: TuxemonMap, path: str
    ) -> None:
        """
        Processes and merges events from YAML files into the map.

        Parameters:
            txmn_map: The TuxemonMap object to update.
            path: The path to the TMX map file for deriving YAML paths.
        """
        yaml_files = [Path(path).with_suffix(".yaml")]
        if txmn_map.scenario:
            _scenario = prepare.fetch("maps", f"{txmn_map.scenario}.yaml")
            yaml_files.append(Path(_scenario))

        yaml_collision, events = self._process_events(yaml_files)
        self._merge_events(txmn_map, yaml_collision, events)


class YAMLEventLoader:
    """Support for reading game events from a YAML file."""

    def load_collision(
        self, path: str
    ) -> MutableMapping[tuple[int, int], Optional[RegionProperties]]:
        """
        Load collision data from a YAML file.

        This function reads a YAML file at the specified path and extracts collision
        data from it. The collision data is used to create a dictionary of coordinates
        that represent the collision areas.

        Parameters:
            path: Path to the file.

        Returns:
            A dictionary with collision coordinates as keys.
        """
        yaml_data: dict[str, list[dict[str, Any]]] = parse_yaml(path)

        collision_dict: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ] = {}

        if "collisions" in yaml_data:
            for collision_data in yaml_data["collisions"]:
                x = int(collision_data.get("x", 0))
                y = int(collision_data.get("y", 0))
                w = int(collision_data.get("width", 1))
                h = int(collision_data.get("height", 1))
                event_type = str(collision_data.get("type"))
                coords = [(x + i, y + j) for i in range(w) for j in range(h)]
                for coord in coords:
                    collision_dict[coord] = None
        return collision_dict

    def load_events(
        self, path: str, source: str
    ) -> dict[str, list[EventObject]]:
        """
        Load EventObjects from a YAML file.

        This function reads a YAML file at the specified path and extracts EventObject
        instances from it. The EventObjects are filtered by the specified source type
        (either "event" or "init").

        Parameters:
            path: Path to the file.
            source: The type of events to load (either "event" or "init").

        Returns:
            A dictionary with "events" and "inits" as keys, each containing a list
            of EventObject instances.
        """
        yaml_data: dict[str, dict[str, dict[str, Any]]] = parse_yaml(path)

        events_dict: dict[str, list[EventObject]] = {"event": [], "init": []}

        for name, event_data in yaml_data["events"].items():
            _id = uuid.uuid4().int
            conds = []
            acts = []
            x = event_data.get("x", 0)
            y = event_data.get("y", 0)
            w = event_data.get("width", 1)
            h = event_data.get("height", 1)
            event_type = str(event_data.get("type"))

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

            if event_type == source:
                event = EventObject(_id, name, x, y, w, h, conds, acts)
                events_dict[event_type].append(event)

        return events_dict


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
        data = self.load_tiled_map(filename)
        tile_size = (data.tilewidth, data.tileheight)
        data.tilewidth, data.tileheight = prepare.TILE_SIZE

        collision_map, collision_lines_map = self.load_collision_data(
            data, tile_size
        )
        surface_map = self.load_surface_data(data)
        events, inits = self.load_events_and_inits(data, tile_size)

        return TuxemonMap(
            events,
            inits,
            surface_map,
            collision_map,
            collision_lines_map,
            data,
            data.properties,
            filename,
        )

    def load_tiled_map(self, filename: str) -> pytmx.TiledMap:
        return pytmx.TiledMap(
            filename=filename,
            image_loader=self.image_loader,
            pixelalpha=True,
        )

    def load_collision_data(
        self, data: pytmx.TiledMap, tile_size: tuple[int, int]
    ) -> tuple[
        dict[tuple[int, int], Optional[RegionProperties]],
        set[tuple[tuple[int, int], Direction]],
    ]:
        collision_map: dict[tuple[int, int], Optional[RegionProperties]] = {}
        collision_lines_map: set[tuple[tuple[int, int], Direction]] = set()
        gids_with_props = {}
        gids_with_colliders = {}

        for gid, props in data.tile_properties.items():
            conds = extract_region_properties(props)
            gids_with_props[gid] = conds if conds else None
            colliders = props.get("colliders")
            if colliders is not None:
                gids_with_colliders[gid] = colliders

        for layer in data.visible_tile_layers:
            layer = data.layers[layer]
            for x, y, gid in layer.iter_data():
                tile_props = gids_with_props.get(gid)
                if tile_props is not None:
                    collision_map[(x, y)] = tile_props
                colliders = gids_with_colliders.get(gid)
                if colliders is not None:
                    for obj in colliders:
                        self.process_collision_object(
                            obj,
                            tile_size,
                            collision_map,
                            collision_lines_map,
                            x,
                            y,
                        )

        for obj in data.objects:
            if obj.type and obj.type.lower().startswith("collision"):
                for tile_position, props in self.extract_tile_collisions(
                    obj, tile_size
                ):
                    collision_map[tile_position] = props
                for line in self.collision_lines_from_object(obj, tile_size):
                    collision_lines_map.add(line)

        return collision_map, collision_lines_map

    def load_surface_data(
        self, data: pytmx.TiledMap
    ) -> dict[tuple[int, int], dict[str, float]]:
        surface_map = {}
        gids_with_surface: dict[int, Any] = {}

        for gid, props in data.tile_properties.items():
            for surface_key in prepare.SURFACE_KEYS:
                surface = props.get(surface_key)
                if surface is not None:
                    if gid not in gids_with_surface:
                        gids_with_surface[gid] = {}
                    gids_with_surface[gid][surface_key] = surface

        for layer in data.visible_tile_layers:
            layer = data.layers[layer]
            for x, y, gid in layer.iter_data():
                surface = gids_with_surface.get(gid)
                if surface is not None:
                    surface_map[(x, y)] = surface

        return surface_map

    def load_events_and_inits(
        self, data: pytmx.TiledMap, tile_size: tuple[int, int]
    ) -> tuple[list[EventObject], list[EventObject]]:
        events: list[EventObject] = []
        inits: list[EventObject] = []

        for obj in data.objects:
            if obj.type == "event":
                events.append(self.load_event(obj, tile_size))
            elif obj.type == "init":
                inits.append(self.load_event(obj, tile_size))

        return events, inits

    def process_collision_object(
        self,
        obj: pytmx.TiledObject,
        tile_size: tuple[int, int],
        collision_map: dict[tuple[int, int], Optional[RegionProperties]],
        collision_lines_map: set[tuple[tuple[int, int], Direction]],
        x: int,
        y: int,
    ) -> None:
        if obj.type and obj.type.lower().startswith("collision"):
            if getattr(obj, "closed", True):
                region_conditions = copy_dict_with_keys(
                    obj.properties, region_properties
                )
                _extract = extract_region_properties(region_conditions)
                collision_map[(x, y)] = _extract
            for line in self.collision_lines_from_object(obj, tile_size):
                coords, direction = line
                lx, ly = coords
                collision_lines_map.add(((lx + x, ly + y), direction))

    def extract_tile_collisions(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[RegionTile, None, None]:
        """ "Extract tile collisions from a Tiled object."""
        if getattr(tiled_object, "closed", True):
            yield from self.region_tiles(tiled_object, tile_size)

    def collision_lines_from_object(
        self,
        tiled_object: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[tuple[tuple[int, int], Direction], None, None]:
        """Generate collision lines from a Tiled object."""
        # TODO: test dropping "collision_lines_map" and replacing with "enter/exit" tiles
        if not getattr(tiled_object, "closed", True):
            for blocker0, blocker1, orientation in self.process_line(
                tiled_object, tile_size
            ):
                if orientation == Orientation.vertical:
                    yield blocker0, Direction.left
                    yield blocker1, Direction.right
                elif orientation == Orientation.horizontal:
                    yield blocker1, Direction.down
                    yield blocker0, Direction.up
                else:
                    raise ValueError(f"Invalid orientation: {orientation}")

    def process_line(
        self,
        line: pytmx.TiledObject,
        tile_size: tuple[int, int],
    ) -> Generator[
        tuple[tuple[int, int], tuple[int, int], Orientation], None, None
    ]:
        """Identify the tiles on either side of the line and block movement along it."""
        if len(line.points) < 2:
            raise ValueError("Collision lines must have at least 2 points")

        for point_0, point_1 in zip(line.points, line.points[1:]):
            p0 = point_to_grid(point_0, tile_size)
            p1 = point_to_grid(point_1, tile_size)
            p0, p1 = sorted((p0, p1))
            angle = angle_of_points(p0, p1)
            orientation = orientation_by_angle(angle)

            for i in bresenham(p0[0], p0[1], p1[0], p1[1], include_end=False):
                angle1 = angle - (pi / 2)
                other = (
                    int(round(cos(angle1) + i[0])),
                    int(round(sin(angle1) + i[1])),
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
            region.properties, region_properties
        )
        rect = snap_rect(
            Rect((region.x, region.y, region.width, region.height)), grid_size
        )
        for tile_x, tile_y in tiles_inside_rect(rect, grid_size):
            yield (tile_x, tile_y), extract_region_properties(
                region_conditions
            )

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
        event_id = uuid.uuid4().int
        conditions = []
        actions = []
        x, y, w, h = (
            int(obj.x / tile_size[0]),
            int(obj.y / tile_size[1]),
            int(obj.width / tile_size[0]),
            int(obj.height / tile_size[1]),
        )

        properties = obj.properties
        for key, value in natsorted(properties.items()):
            if not isinstance(key, str):
                continue
            if key.startswith("cond"):
                operator, cond_type, args = parse_condition_string(value)
                conditions.append(
                    MapCondition(cond_type, args, x, y, w, h, operator, key)
                )
            elif key.startswith("act"):
                act_type, args = parse_action_string(value)
                actions.append(MapAction(act_type, args, key))
            elif key.startswith("behav"):
                behav_type, args = parse_behav_string(value)
                conditions.insert(
                    0,
                    MapCondition(
                        "behav", [behav_type, *args], x, y, w, h, "is", key
                    ),
                )
                actions.insert(
                    0, MapAction("behav", [":".join([behav_type, *args])], key)
                )

        return EventObject(event_id, obj.name, x, y, w, h, conditions, actions)
