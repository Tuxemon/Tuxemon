# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

import yaml

from tuxemon.constants import paths
from tuxemon.db import Direction
from tuxemon.event import EventObject
from tuxemon.event.eventengine import EventEngine
from tuxemon.map import RegionProperties, TuxemonMap

logger = logging.getLogger(__name__)


@dataclass
class MapType:
    name: str = "notype"


def load_map_types(filename: str) -> list[MapType]:
    yaml_path = f"{paths.mods_folder}/{filename}"
    """Loads map types from a YAML file and returns a list of MapType instances."""
    with open(yaml_path, encoding="utf-8") as file:
        data = yaml.safe_load(file)
        return [MapType(**entry) for entry in data.get("map_types", [])]


MAP_TYPES = load_map_types("map_types.yaml")
map_types_list = [mt.name for mt in MAP_TYPES]


class MapManager:
    def __init__(self, event_engine: EventEngine):
        """Manages map loading and properties while ensuring event resets."""
        self.event_engine = event_engine
        self.events: Sequence[EventObject] = []
        self.inits: list[EventObject] = []
        self.current_map: Optional[TuxemonMap] = None
        self.maps: dict[str, Any] = {}
        self.map_slug = ""
        self.map_name = ""
        self.map_desc = ""
        self.map_inside = False
        self.map_size: tuple[int, int] = (0, 0)
        self.map_type = MapType()
        self.map_north = ""
        self.map_south = ""
        self.map_east = ""
        self.map_west = ""
        self.collision_lines_map: set[tuple[tuple[int, int], Direction]] = (
            set()
        )
        self.surface_map: MutableMapping[tuple[int, int], dict[str, float]] = (
            {}
        )
        self.collision_map: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ] = {}

    def load_map(self, map_data: TuxemonMap) -> None:
        """Loads a new map, updates properties, and resets relevant events."""
        self.current_map = map_data
        self.events = map_data.events
        self.inits = list(map_data.inits)
        self.maps = map_data.maps
        self.map_slug = map_data.slug
        self.map_name = map_data.name
        self.map_desc = map_data.description
        self.map_inside = map_data.inside
        self.map_size = map_data.size
        self.collision_lines_map = map_data.collision_lines_map
        self.collision_map = map_data.collision_map
        self.surface_map = map_data.surface_map

        # Reset and update event system
        self.event_engine.reset()
        self.event_engine.set_current_map(map_data)

        valid_map_types = {mt.name for mt in MAP_TYPES}
        if map_data.map_type in valid_map_types:
            self.map_type = next(
                mt for mt in MAP_TYPES if mt.name == map_data.map_type
            )
        else:
            logger.warning(
                f"Invalid map type '{map_data.map_type}', defaulting to {self.map_type.name}."
            )

        # Cardinal directions
        self.map_north = map_data.north_trans
        self.map_south = map_data.south_trans
        self.map_east = map_data.east_trans
        self.map_west = map_data.west_trans

    def get_map_filepath(self) -> Optional[str]:
        """Returns the filepath of the current map."""
        if self.current_map:
            return self.current_map.filename
        return None

    def is_in_location_type(self, location_type: str) -> bool:
        """Checks if the current map type matches a given location type."""
        return (
            self.current_map is not None
            and self.map_type.name == location_type
        )
