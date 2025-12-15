# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import yaml

from tuxemon.constants import paths
from tuxemon.db import Direction

if TYPE_CHECKING:
    from tuxemon.db import EventObject
    from tuxemon.map.map_region import RegionProperties
    from tuxemon.map.map_tuxemon import AbstractMap

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MapType:
    name: str = "notype"


def load_map_types(filename: str) -> defaultdict[str, MapType]:
    """Loads map types from a YAML file and returns a defaultdict mapping name -> MapType."""
    yaml_path = paths.mods_folder / filename
    try:
        with yaml_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return defaultdict(
                lambda: MapType(name="notype"),
                {
                    entry["name"]: MapType(**entry)
                    for entry in data.get("map_types", [])
                    if "name" in entry
                },
            )
    except FileNotFoundError:
        logger.warning(f"Map types file not found at {yaml_path}")
    except Exception as e:
        logger.error(f"Error loading map types: {e}")

    return defaultdict(
        lambda: MapType(name="notype"), {"notype": MapType(name="notype")}
    )


MAP_TYPES = load_map_types("map_types.yaml")


class MapManager:
    """
    Manages the active map state.

    Access to map properties is proxied through this manager for safety and encapsulation.
    """

    def __init__(self) -> None:
        """Initializes the manager state with no map loaded."""
        self.current_map: Optional[AbstractMap] = None
        self.maps: dict[str, Any] = {}
        self._map_type_slug: Optional[str] = None

    @property
    def map_slug(self) -> str:
        """The unique slug of the current map."""
        return self.current_map.slug if self.current_map else ""

    @property
    def map_name(self) -> str:
        """The translated name of the current map."""
        return (
            self.current_map.name if self.current_map else "Unknown Location"
        )

    @property
    def map_desc(self) -> str:
        """The translated description of the current map."""
        return self.current_map.description if self.current_map else ""

    @property
    def map_inside(self) -> bool:
        """True if the current map is marked as an indoor location."""
        return self.current_map.is_inside if self.current_map else False

    @property
    def map_size(self) -> tuple[int, int]:
        """The width and height of the current map in tiles."""
        return self.current_map.size if self.current_map else (0, 0)

    @property
    def collision_lines_map(self) -> set[tuple[tuple[int, int], Direction]]:
        """A set of collision lines/edges on the current map."""
        return (
            self.current_map.collision_lines_map if self.current_map else set()
        )

    @property
    def surface_map(self) -> MutableMapping[tuple[int, int], dict[str, float]]:
        """Map of tile coordinates to surface properties (e.g., speed modifiers)."""
        return self.current_map.surface_map if self.current_map else {}

    @property
    def collision_map(
        self,
    ) -> MutableMapping[tuple[int, int], Optional[RegionProperties]]:
        """Map of tile coordinates to collision/region properties."""
        return self.current_map.collision_map if self.current_map else {}

    @property
    def map_north(self) -> str:
        return self.current_map.north_trans if self.current_map else ""

    @property
    def map_south(self) -> str:
        return self.current_map.south_trans if self.current_map else ""

    @property
    def map_east(self) -> str:
        return self.current_map.east_trans if self.current_map else ""

    @property
    def map_west(self) -> str:
        return self.current_map.west_trans if self.current_map else ""

    @property
    def map_type(self) -> MapType:
        """Returns the full MapType object for the current map."""
        if self._map_type_slug and self._map_type_slug in MAP_TYPES:
            return MAP_TYPES[self._map_type_slug]
        logger.warning(
            f"Invalid or missing map type slug '{self._map_type_slug}', defaulting to 'notype'."
        )
        return MapType(name="notype")

    @property
    def events(self) -> Sequence[EventObject]:
        return self.current_map.events if self.current_map else []

    @property
    def inits(self) -> Sequence[EventObject]:
        return self.current_map.inits if self.current_map else []

    def load_map(self, map_data: AbstractMap) -> None:
        """Loads a new map, sets properties, and resets relevant events."""
        self.current_map = map_data
        self.maps = map_data.maps
        self._map_type_slug = map_data.map_type

        map_data.add_events([])
        map_data.add_inits([])

        if map_data.map_type not in MAP_TYPES:
            logger.warning(
                f"Invalid map type '{map_data.map_type}', defaulting to 'notype'."
            )

    def set_events(self, new_events: Sequence[EventObject]) -> None:
        if self.current_map:
            self.current_map.add_events(new_events)

    def set_inits(self, new_inits: Sequence[EventObject]) -> None:
        if self.current_map:
            self.current_map.add_inits(new_inits)

    def clear_events(self) -> None:
        if self.current_map:
            self.current_map.clear_events()

    def clear_inits(self) -> None:
        if self.current_map:
            self.current_map.clear_inits()

    def remove_event(self, event: EventObject) -> None:
        if self.current_map:
            updated = list(self.current_map.events)
            updated.remove(event)
            self.current_map.add_events(updated)

    def remove_init(self, event: EventObject) -> None:
        if self.current_map:
            updated = list(self.current_map.inits)
            updated.remove(event)
            self.current_map.add_inits(updated)

    def get_map_filepath(self) -> Optional[str]:
        """Returns the filepath of the current map."""
        if self.current_map:
            return self.current_map.filename
        return None

    def is_in_location_type(self, location_type: str) -> bool:
        """Checks if the current map type matches a given location type."""
        return self.map_type.name == location_type
