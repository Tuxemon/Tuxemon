# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pyscroll
from pytmx import pytmx
from pytmx.pytmx import TiledMap

from tuxemon.graphics import scaled_image_loader
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.db import Direction, EventObject
    from tuxemon.map.region import RegionProperties

logger = logging.getLogger(__name__)


@dataclass
class MapConfig:
    slug: str = ""
    edges: str | None = None
    inside: bool = False
    scenario: str | None = None
    map_type: str | None = None
    cardinal_directions: dict[str, str] = field(
        default_factory=lambda: {
            "north": "-",
            "south": "-",
            "east": "-",
            "west": "-",
        }
    )


class AbstractMap(ABC):
    @property
    @abstractmethod
    def slug(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def size(self) -> tuple[int, int]: ...

    @property
    @abstractmethod
    def area(self) -> int: ...

    @property
    @abstractmethod
    def is_inside(self) -> bool: ...

    @property
    @abstractmethod
    def map_type(self) -> str | None: ...

    @property
    @abstractmethod
    def collision_map(
        self,
    ) -> MutableMapping[tuple[int, int], Any | None]: ...

    @property
    @abstractmethod
    def surface_map(
        self,
    ) -> MutableMapping[tuple[int, int], dict[str, float]]: ...

    @property
    @abstractmethod
    def collision_lines_map(self) -> set[tuple[tuple[int, int], Any]]: ...

    @property
    @abstractmethod
    def events(self) -> Sequence[EventObject]: ...

    @property
    @abstractmethod
    def inits(self) -> Sequence[EventObject]: ...

    @property
    @abstractmethod
    def maps(self) -> dict[str, Any]: ...

    @property
    @abstractmethod
    def filename(self) -> str: ...

    @property
    @abstractmethod
    def north_trans(self) -> str: ...

    @property
    @abstractmethod
    def south_trans(self) -> str: ...

    @property
    @abstractmethod
    def east_trans(self) -> str: ...

    @property
    @abstractmethod
    def west_trans(self) -> str: ...

    @property
    @abstractmethod
    def renderer(self) -> Any | None: ...

    @property
    @abstractmethod
    def sprite_layer(self) -> int: ...

    @property
    @abstractmethod
    def scenario(self) -> str | None: ...

    @abstractmethod
    def initialize_renderer(self) -> None: ...

    @abstractmethod
    def reload_tiles(self) -> None: ...

    @abstractmethod
    def add_events(self, new_events: Sequence[EventObject]) -> None:
        """Append new events to the existing events list."""

    @abstractmethod
    def add_inits(self, new_inits: Sequence[EventObject]) -> None:
        """Append new init events to the existing inits list."""

    @abstractmethod
    def remove_init(self, event: EventObject) -> None: ...

    @abstractmethod
    def remove_event(self, event: EventObject) -> None: ...
    @abstractmethod
    def clear_events(self) -> None: ...

    @abstractmethod
    def clear_inits(self) -> None: ...


class TuxemonMap(AbstractMap):
    """
    Contains collisions geometry and events loaded from a file.

    Supports entity movement and pathfinding.
    """

    SPRITE_LAYER_INDEX = 2

    def __init__(
        self,
        events: Sequence[EventObject],
        inits: Sequence[EventObject],
        surface_map: MutableMapping[tuple[int, int], dict[str, float]],
        collision_map: MutableMapping[
            tuple[int, int], RegionProperties | None
        ],
        collisions_lines_map: set[tuple[tuple[int, int], Direction]],
        tiled_map: TiledMap,
        maps: dict[str, Any],
        filename: str,
        resolution: tuple[int, int],
    ) -> None:
        self._collision_map = collision_map
        self._surface_map = surface_map
        self._collision_lines_map = collisions_lines_map
        self._data = tiled_map
        self._filename = filename
        self._resolution = resolution
        self._maps = maps
        self._renderer: pyscroll.BufferedRenderer | None = None

        self._events: list[EventObject] = list(events)
        self._inits: list[EventObject] = list(inits)

        self._config = self._parse_config(maps)

    def _parse_config(self, maps: dict[str, Any]) -> MapConfig:
        def translate_cardinals(direction: str) -> str:
            raw = maps.get(direction, "-")
            return " - ".join(T.translate(c) for c in raw.split(","))

        return MapConfig(
            slug=maps.get("slug", ""),
            edges=maps.get("edges"),
            inside=bool(maps.get("inside")),
            scenario=(
                str(maps.get("scenario")) if maps.get("scenario") else None
            ),
            map_type=maps.get("map_type"),
            cardinal_directions={
                "north": translate_cardinals("north"),
                "south": translate_cardinals("south"),
                "east": translate_cardinals("east"),
                "west": translate_cardinals("west"),
            },
        )

    @property
    def slug(self) -> str:
        return self._config.slug

    @property
    def maps(self) -> dict[str, Any]:
        return self._maps

    @property
    def width(self) -> int:
        return int(self._data.width)

    @property
    def height(self) -> int:
        return int(self._data.height)

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def collision_map(
        self,
    ) -> MutableMapping[tuple[int, int], RegionProperties | None]:
        return self._collision_map

    @property
    def surface_map(self) -> MutableMapping[tuple[int, int], dict[str, float]]:
        return self._surface_map

    @property
    def collision_lines_map(self) -> set[tuple[tuple[int, int], Direction]]:
        return self._collision_lines_map

    @property
    def renderer(self) -> pyscroll.BufferedRenderer | None:
        return self._renderer

    @property
    def events(self) -> Sequence[EventObject]:
        return self._events

    @property
    def inits(self) -> Sequence[EventObject]:
        return self._inits

    @property
    def sprite_layer(self) -> int:
        return self.SPRITE_LAYER_INDEX

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def is_inside(self) -> bool:
        return self._config.inside

    @property
    def north_trans(self) -> str:
        return self._config.cardinal_directions["north"]

    @property
    def south_trans(self) -> str:
        return self._config.cardinal_directions["south"]

    @property
    def east_trans(self) -> str:
        return self._config.cardinal_directions["east"]

    @property
    def west_trans(self) -> str:
        return self._config.cardinal_directions["west"]

    @property
    def name(self) -> str:
        return T.translate(self._config.slug)

    @property
    def description(self) -> str:
        return T.translate(f"{self._config.slug}_description")

    @property
    def scenario(self) -> str | None:
        return self._config.scenario

    @property
    def map_type(self) -> str | None:
        return self._config.map_type

    def initialize_renderer(self) -> None:
        visual_data = pyscroll.data.TiledMapData(self._data)
        clamp = self._config.edges == "clamped"
        self._renderer = pyscroll.BufferedRenderer(
            visual_data,
            self._resolution,
            clamp_camera=clamp,
            tall_sprites=self.SPRITE_LAYER_INDEX,
        )

    def add_events(self, new_events: Sequence[EventObject]) -> None:
        self._events.extend(new_events)

    def add_inits(self, new_inits: Sequence[EventObject]) -> None:
        self._inits.extend(new_inits)

    def remove_init(self, event: EventObject) -> None:
        self._inits.remove(event)

    def remove_event(self, event: EventObject) -> None:
        self._events.remove(event)

    def clear_events(self) -> None:
        self._events.clear()

    def clear_inits(self) -> None:
        self._inits.clear()

    def reload_tiles(self) -> None:
        """Reload the map tiles."""
        if self.renderer is None:
            raise RuntimeError(
                "Renderer must be initialized before reloading tiles"
            )

        data = pytmx.TiledMap(
            self._data.filename,
            image_loader=scaled_image_loader,
            pixelalpha=True,
        )
        self.renderer.data.tmx.images = data.images
        assert self.renderer._buffer
        self.renderer.redraw_tiles(self.renderer._buffer)


class NullMap(AbstractMap):
    """A no-op map object to safely initialize the WorldState when no map file is loaded."""

    def __init__(self) -> None:
        self._events: list[EventObject] = []
        self._inits: list[EventObject] = []

    @property
    def slug(self) -> str:
        return "null_map"

    @property
    def name(self) -> str:
        return "Loading Screen"

    @property
    def description(self) -> str:
        return "The world is initializing."

    @property
    def size(self) -> tuple[int, int]:
        return (10, 10)

    @property
    def area(self) -> int:
        return 100

    @property
    def is_inside(self) -> bool:
        return False

    @property
    def map_type(self) -> str | None:
        return "notype"

    @property
    def collision_map(self) -> MutableMapping[tuple[int, int], Any | None]:
        return {}

    @property
    def surface_map(self) -> MutableMapping[tuple[int, int], dict[str, float]]:
        return {}

    @property
    def collision_lines_map(self) -> set[tuple[tuple[int, int], Any]]:
        return set()

    @property
    def events(self) -> Sequence[EventObject]:
        return self._events

    @property
    def inits(self) -> Sequence[EventObject]:
        return self._inits

    @property
    def maps(self) -> dict[str, Any]:
        return {}

    @property
    def filename(self) -> str:
        return "null_map.tmx"

    @property
    def north_trans(self) -> str:
        return ""

    @property
    def south_trans(self) -> str:
        return ""

    @property
    def east_trans(self) -> str:
        return ""

    @property
    def west_trans(self) -> str:
        return ""

    @property
    def renderer(self) -> Any | None:
        return None

    @property
    def sprite_layer(self) -> int:
        return 2

    @property
    def scenario(self) -> str | None:
        return None

    def initialize_renderer(self) -> None:
        pass

    def reload_tiles(self) -> None:
        pass

    def add_events(self, new_events: Sequence[EventObject]) -> None:
        self._events.extend(new_events)

    def add_inits(self, new_inits: Sequence[EventObject]) -> None:
        self._inits.extend(new_inits)

    def remove_init(self, event: EventObject) -> None:
        self._inits.remove(event)

    def remove_event(self, event: EventObject) -> None:
        self._events.remove(event)

    def clear_events(self) -> None:
        self._events.clear()

    def clear_inits(self) -> None:
        self._inits.clear()
