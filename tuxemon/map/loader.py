# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import OrderedDict, defaultdict
from collections.abc import Generator, MutableMapping
from math import cos, pi, sin
from pathlib import Path
from typing import Any

import pytmx
from natsort import natsorted

from tuxemon.compat import Rect
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.constants.paths import mods_folder
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.db import BoundingBox, Direction, EventObject, Orientation
from tuxemon.event.eventparser import EventParser
from tuxemon.graphics import scaled_image_loader
from tuxemon.lib.bresenham import bresenham
from tuxemon.map.map import (
    angle_of_points,
    orientation_by_angle,
    point_to_grid,
    snap_rect,
    tiles_inside_rect,
)
from tuxemon.map.region import RegionProperties, extract_region_properties
from tuxemon.map.tuxemon import AbstractMap, NullMap, TuxemonMap
from tuxemon.platform.const.sizes import (
    MAP_CACHE_SIZE,
    REGION_KEYS,
    SURFACE_KEYS,
)
from tuxemon.prepare import DisplayContext
from tuxemon.tools import copy_dict_with_keys

logger = logging.getLogger(__name__)

RegionTile = tuple[
    tuple[int, int],
    RegionProperties | None,
]


class MapLoader:
    """
    Orchestrates the loading of map data with an integrated LRU caching system.
    """

    def __init__(
        self,
        context: DisplayContext,
        cache_size: int | None = None,
        enable_cache: bool = True,
    ) -> None:
        """
        Initializes the MapLoader with optional cache configuration.

        Parameters:
            cache_size: Maximum number of maps to retain in the LRU cache.
                        If None, defaults to MAP_CACHE_SIZE.
            enable_cache: Flag to enable or disable caching behavior.
                        If False, maps are always loaded fresh from disk.
        """
        self.context = context
        self.tmx_loader = TMXMapLoader()
        self.yaml_loader = YAMLEventLoader()
        self.cache_size = cache_size or MAP_CACHE_SIZE
        self.enable_cache = enable_cache
        self._cache: OrderedDict[str, AbstractMap] = OrderedDict()

    def load_map_data(self, path: str) -> AbstractMap:
        """
        Loads map data, checking the cache first for performance.
        If path is None, returns a NullMap with optional event loading.

        Parameters:
            path: Path to the TMX map file.
        """
        name = Path(path).stem

        resolved = fetch_asset("maps", f"{name}.tmx")
        if not resolved:
            raise FileNotFoundError(f"Map '{name}' not found in assets.")

        normalized_path = str(Path(resolved).resolve())

        if self.enable_cache:
            cached = self.get_cached_map(normalized_path)
            if cached:
                return cached

        txmn_map = self.load_map_from_disk(normalized_path)
        yaml_files = self.resolve_yaml_files(txmn_map, normalized_path)
        self.process_and_merge_events(txmn_map, yaml_files)

        if self.enable_cache:
            self.update_cache(normalized_path, txmn_map)

        return txmn_map

    def load_null_map(self, yaml_path: str | None) -> AbstractMap:
        logger.debug("Loading NullMap with optional events.")
        null_map = NullMap()
        if yaml_path:
            file = mods_folder / yaml_path
            self.process_and_merge_events(null_map, [file])
        return null_map

    def get_cached_map(self, normalized_path: str) -> AbstractMap | None:
        if normalized_path in self._cache:
            logger.debug(f"Cache hit for map '{normalized_path}'.")
            map_data = self._cache.pop(normalized_path)
            self._cache[normalized_path] = map_data
            return map_data
        return None

    def load_map_from_disk(self, normalized_path: str) -> AbstractMap:
        logger.info(
            f"Cache miss for map '{normalized_path}'. Loading from disk."
        )
        return self.tmx_loader.load(normalized_path, self.context)

    def resolve_yaml_files(
        self, txmn_map: AbstractMap, normalized_path: str
    ) -> list[Path]:
        yaml_files = [Path(normalized_path).with_suffix(".yaml")]
        if txmn_map.scenario:
            _scenario = fetch_asset("maps", f"{txmn_map.scenario}.yaml")
            yaml_files.append(Path(_scenario))
        return yaml_files

    def update_cache(
        self, normalized_path: str, map_data: AbstractMap
    ) -> None:
        self._cache[normalized_path] = map_data
        if len(self._cache) > self.cache_size:
            evicted_path, _ = self._cache.popitem(last=False)
            logger.debug(
                f"Cache full. Evicted least recently used map: '{evicted_path}'."
            )

    def process_and_merge_events(
        self, txmn_map: AbstractMap, yaml_files: list[Path]
    ) -> None:
        """
        Processes and merges events from YAML files into the map.

        Parameters:
            txmn_map: The AbstractMap object to update.
            yaml_files: List of YAML file paths to load events from.
        """
        yaml_collision, events = self._process_events(yaml_files)
        self._merge_events(txmn_map, yaml_collision, events)

    def _process_events(
        self, yaml_files: list[Path]
    ) -> tuple[
        MutableMapping[tuple[int, int], RegionProperties | None],
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
            tuple[int, int], RegionProperties | None
        ] = {}
        events: defaultdict[str, list[EventObject]] = defaultdict(list)

        for yaml_file in yaml_files:
            if yaml_file.exists():
                try:
                    yaml_collision.update(
                        self.yaml_loader.load_collision(yaml_file)
                    )
                    events["event"].extend(
                        self.yaml_loader.load_events(yaml_file, "event")[
                            "event"
                        ]
                    )
                    events["init"].extend(
                        self.yaml_loader.load_events(yaml_file, "init")["init"]
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load events from {yaml_file}: {e}"
                    )
            else:
                logger.warning(f"YAML file {yaml_file} not found")

        return yaml_collision, events

    def _merge_events(
        self,
        txmn_map: AbstractMap,
        yaml_collision: MutableMapping[
            tuple[int, int], RegionProperties | None
        ],
        events: dict[str, list[EventObject]],
    ) -> None:
        """
        Merges processed events into the AbstractMap.

        Parameters:
            txmn_map: The AbstractMap object to update.
            yaml_collision: Collision event data.
            events: Dictionary containing events and init sequences.
        """
        logger.debug(f"TMX events before merging: {len(txmn_map.events)}")
        logger.debug(f"TMX inits before merging: {len(txmn_map.inits)}")
        txmn_map.collision_map.update(yaml_collision)
        txmn_map.add_events(events["event"])
        txmn_map.add_inits(events["init"])

    def add_to_cache(self, path: str, map_data: AbstractMap) -> None:
        if not self.enable_cache:
            logger.debug("Caching disabled. Skipping manual insert.")
            return
        normalized_path = str(Path(path).resolve())
        self._cache.pop(normalized_path, None)
        self._cache[normalized_path] = map_data
        if len(self._cache) > self.cache_size:
            evicted_path, _ = self._cache.popitem(last=False)
            logger.debug(f"Evicted LRU map: '{evicted_path}'.")

    def remove_from_cache(self, path: str) -> bool:
        normalized_path = str(Path(path).resolve())
        if normalized_path in self._cache:
            self._cache.pop(normalized_path)
            return True
        return False

    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enables or disables caching behavior at runtime.

        Parameters:
            enabled: True to enable caching, False to disable.
        """
        self.enable_cache = enabled
        logger.info(f"Map caching {'enabled' if enabled else 'disabled'}.")

    def cache_info(self) -> dict[str, Any]:
        """
        Returns cache statistics for introspection.

        Returns:
            Dictionary with current cache size and cached map keys.
        """
        return {
            "enabled": self.enable_cache,
            "size": len(self._cache),
            "keys": list(self._cache.keys()),
        }

    def clear_cache(self) -> None:
        """
        Clears the entire map cache.
        """
        self._cache.clear()
        logger.info("Map cache cleared.")


class YAMLEventLoader:
    """Support for reading game events from a YAML file."""

    def load_collision(
        self, path: Path
    ) -> MutableMapping[tuple[int, int], RegionProperties | None]:
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
        yaml_data: dict[str, list[dict[str, Any]]] = load_yaml(path)

        collision_dict: MutableMapping[
            tuple[int, int], RegionProperties | None
        ] = {}

        if "collisions" in yaml_data:
            for collision_data in yaml_data["collisions"]:
                x = int(collision_data.get("x", 0))
                y = int(collision_data.get("y", 0))
                w = int(collision_data.get("width", 1))
                h = int(collision_data.get("height", 1))
                coords = [(x + i, y + j) for i in range(w) for j in range(h)]
                for coord in coords:
                    collision_dict[coord] = None
        return collision_dict

    def load_events(
        self, path: Path, source: str
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
        event_parser = EventParser()
        yaml_data: dict[str, dict[str, dict[str, Any]]] = load_yaml(path)

        events_dict: dict[str, list[EventObject]] = {"event": [], "init": []}

        if source not in ("event", "init"):
            logger.warning(
                f"Unknown event source '{source}', returning empty."
            )
            return events_dict

        for name, event_data in yaml_data["events"].items():
            _event_type = event_data.get("type")
            event_type = str(_event_type) if _event_type is not None else None
            if event_type == source:
                priority = int(event_data.get("priority", 0))
                _timeout = event_data.get("timeout")
                timeout = float(_timeout) if _timeout is not None else None
                _delay = event_data.get("delay")
                delay = float(_delay) if _delay is not None else None
                x, y = event_data.get("x", 0), event_data.get("y", 0)
                w, h = event_data.get("width", 1), event_data.get("height", 1)
                try:
                    box = BoundingBox(x=x, y=y, width=w, height=h)
                except Exception as e:
                    logger.error(
                        f"Invalid bounding box for event '{name}': {e}"
                    )
                    continue
                event = event_parser.create_event_object(
                    event_data, name, box, priority, timeout, delay
                )
                events_dict[event_type].append(event)
        return events_dict


class TMXMapLoader:
    """Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/
    """

    def __init__(self) -> None:
        self.image_loader = scaled_image_loader

    def load(self, filename: str, context: DisplayContext) -> TuxemonMap:
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
        data.tilewidth, data.tileheight = context.tile_size

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
            context.resolution,
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
        dict[tuple[int, int], RegionProperties | None],
        set[tuple[tuple[int, int], Direction]],
    ]:
        collision_map: dict[tuple[int, int], RegionProperties | None] = {}
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
            for surface_key in SURFACE_KEYS:
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
            try:
                if obj.type == "event":
                    events.append(self.load_event(obj, tile_size))
                elif obj.type == "init":
                    inits.append(self.load_event(obj, tile_size))
            except ValueError as e:
                logger.error(f"Skipping event '{obj.name}': {e}")

        return events, inits

    def process_collision_object(
        self,
        obj: pytmx.TiledObject,
        tile_size: tuple[int, int],
        collision_map: dict[tuple[int, int], RegionProperties | None],
        collision_lines_map: set[tuple[tuple[int, int], Direction]],
        x: int,
        y: int,
    ) -> None:
        if obj.type and obj.type.lower().startswith("collision"):
            if getattr(obj, "closed", True):
                region_conditions = copy_dict_with_keys(
                    obj.properties, REGION_KEYS
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
                if orientation == Orientation.VERTICAL:
                    yield blocker0, Direction.LEFT
                    yield blocker1, Direction.RIGHT
                elif orientation == Orientation.HORIZONTAL:
                    yield blocker1, Direction.DOWN
                    yield blocker0, Direction.UP
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
        region_conditions = copy_dict_with_keys(region.properties, REGION_KEYS)
        rect = snap_rect(
            Rect((region.x, region.y, region.width, region.height)), grid_size
        )
        for tile_x, tile_y in tiles_inside_rect(rect, grid_size):
            yield (
                (tile_x, tile_y),
                extract_region_properties(region_conditions),
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
        event_parser = EventParser()
        x, y, w, h = (
            int(obj.x / tile_size[0]),
            int(obj.y / tile_size[1]),
            int(obj.width / tile_size[0]),
            int(obj.height / tile_size[1]),
        )

        raw_props = obj.properties or {}
        event_data: dict[str, Any] = {
            "conditions": [],
            "actions": [],
            "behav": [],
        }

        for key, value in natsorted(raw_props.items()):
            if not isinstance(key, str):
                continue
            if key.startswith("cond"):
                event_data["conditions"].append(value)
            elif key.startswith("act"):
                event_data["actions"].append(value)
            elif key.startswith("behav"):
                event_data["behav"].append(value)

        try:
            box = BoundingBox(x=x, y=y, width=w, height=h)
        except Exception as e:
            raise ValueError(
                f"Invalid bounding box for event '{obj.name}': {e}"
            ) from e

        return event_parser.create_event_object(event_data, obj.name, box)
