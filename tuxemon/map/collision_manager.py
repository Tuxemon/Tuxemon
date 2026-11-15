# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from tuxemon.map.region import RegionProperties

if TYPE_CHECKING:
    from tuxemon.entity.entity import Entity
    from tuxemon.map.manager import MapManager


CollisionMap = Mapping[tuple[int, int], RegionProperties | None]


class CollisionManager:
    """
    Manages collision data and performs collision checks within the game world.
    """

    def __init__(self, map_manager: MapManager) -> None:
        self._map_manager = map_manager
        self._entity_map: dict[tuple[int, int], Entity] = {}

    def check_collision_zones(
        self,
        collision_map: CollisionMap,
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Returns coordinates of specific collision zones.

        Parameters:
            collision_map: The collision map.
            label: The label to filter collision zones by.

        Returns:
            A list of coordinates of collision zones with the specific label.
        """
        return [
            coords
            for coords, props in collision_map.items()
            if props and props.key == label
        ]

    def add_collision(self, entity: Entity, pos: tuple[int, int]) -> None:
        """Register an NPC at a specific tile."""
        self._entity_map[pos] = entity

    def remove_collision(self, pos: tuple[int, int]) -> None:
        """Unregister whatever NPC was at this tile."""
        self._entity_map.pop(pos, None)

    def is_tile_occupied(self, coords: tuple[int, int]) -> bool:
        """Returns True if an entity is registered at the given tile."""
        return coords in self._entity_map

    def get_entity_at(self, coords: tuple[int, int]) -> Entity | None:
        """Returns the entity at the given tile, or None if unoccupied."""
        return self._entity_map.get(coords)

    def get_collision_map(self) -> CollisionMap:
        collision_dict: dict[tuple[int, int], RegionProperties | None] = {}

        # Add surface map entries (impassable surfaces)
        for coords, surface in self._map_manager.surface_map.items():
            for label, value in surface.items():
                if float(value) == 0:
                    region = (
                        self._map_manager.collision_map.get(coords)
                        or RegionProperties()
                    )
                    collision_dict[coords] = region.with_overrides(key=label)

        # Overlay static collision map
        collision_dict.update(self._map_manager.collision_map)

        # Entity-occupied tiles with no terrain data are marked None (blocked)
        # Tiles with terrain data are already in collision_dict and checked separately
        for coords in self._entity_map:
            if coords not in collision_dict:
                collision_dict[coords] = None

        return collision_dict
