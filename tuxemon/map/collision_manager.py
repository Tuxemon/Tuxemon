# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, DefaultDict, Optional, Union

from tuxemon import prepare
from tuxemon.db import Direction
from tuxemon.map.map_region import RegionProperties

if TYPE_CHECKING:

    from tuxemon.entity import Entity
    from tuxemon.map.map_manager import MapManager
    from tuxemon.npc import NPC
    from tuxemon.npc_manager import NPCManager

logger = logging.getLogger(__name__)


CollisionMap = Mapping[
    tuple[int, int],
    Optional[RegionProperties],
]


class CollisionManager:
    """
    Manages collision data and performs collision checks within the game world.
    """

    def __init__(
        self, map_manager: MapManager, npc_manager: NPCManager
    ) -> None:
        self._map_manager = map_manager
        self._npc_manager = npc_manager

    def get_all_tile_properties(
        self,
        surface_map: MutableMapping[tuple[int, int], dict[str, float]],
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Retrieves the coordinates of all tiles with a specific property.

        Parameters:
            map: The surface map.
            label: The label (SurfaceKeys).

        Returns:
            A list of coordinates (tuples) of tiles with the specified label.
        """
        return [
            coords for coords, props in surface_map.items() if label in props
        ]

    def update_tile_property(self, label: str, moverate: float) -> None:
        """
        Updates the movement rate property for existing tile entries in the
        surface map.

        This method modifies the moverate value for tiles that already contain
        the specified label, ensuring that no new dictionary entries are created.
        If the label is not present in a tile's properties, the tile remains
        unchanged. The update process runs efficiently to prevent unnecessary
        modifications.

        Parameters:
            label: The property key to update (e.g., terrain type).
            moverate: The new movement rate value to assign.
        """
        if label not in prepare.SURFACE_KEYS:
            return

        for coord in self.get_all_tile_properties(
            self._map_manager.surface_map, label
        ):
            props = self._map_manager.surface_map.get(coord)
            if props and props.get(label) != moverate:
                props[label] = moverate

    def all_tiles_modified(self, label: str, moverate: float) -> bool:
        """
        Checks if all tiles with the specified label have been modified.

        Parameters:
            label: The property key to check.
            moverate: The expected movement rate.

        Returns:
            True if all tiles have the expected moverate, False otherwise.
        """
        return all(
            self._map_manager.surface_map[coord].get(label) == moverate
            for coord in self.get_all_tile_properties(
                self._map_manager.surface_map, label
            )
        )

    def check_collision_zones(
        self,
        collision_map: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ],
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

    def add_collision(
        self,
        entity: Entity[Any],
        pos: Sequence[float],
    ) -> None:
        """
        Registers the given entity's position within the collision zone.

        Parameters:
            entity: The entity object to be added to the collision zone.
            pos: The X, Y coordinates (as floats) indicating the entity's position.
        """
        coords = (int(pos[0]), int(pos[1]))
        region = self._map_manager.collision_map.get(coords)

        enter_from = region.enter_from if region else []
        exit_from = region.exit_from if region else []
        endure = region.endure if region else []
        key = region.key if region else None
        push_effect = region.push_effect if region else None
        speed_modifier = region.speed_modifier if region else None

        prop = RegionProperties(
            enter_from=enter_from,
            exit_from=exit_from,
            endure=endure,
            entity=entity,
            key=key,
            push_effect=push_effect,
            speed_modifier=speed_modifier,
        )

        self._map_manager.collision_map[coords] = prop

    def remove_collision(self, tile_pos: tuple[int, int]) -> None:
        """
        Removes the specified tile position from the collision zone.

        Parameters:
            tile_pos: The X, Y tile coordinates to be removed from the collision map.
        """
        region = self._map_manager.collision_map.get(tile_pos)
        if not region:
            return  # Nothing to remove

        if region.enter_from or region.exit_from or region.endure:
            prop = RegionProperties(
                enter_from=region.enter_from,
                exit_from=region.exit_from,
                endure=region.endure,
                key=region.key,
                push_effect=region.push_effect,
                speed_modifier=region.speed_modifier,
            )
            self._map_manager.collision_map[tile_pos] = prop
        else:
            # Remove region
            del self._map_manager.collision_map[tile_pos]

    def add_collision_label(self, label: str) -> None:
        coords = self.check_collision_zones(
            self._map_manager.collision_map, label
        )
        properties = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[],
            key=label,
        )
        if coords:
            for coord in coords:
                self._map_manager.collision_map[coord] = properties

    def add_collision_position(
        self, label: str, position: tuple[int, int]
    ) -> None:
        properties = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[],
            key=label,
        )
        self._map_manager.collision_map[position] = properties

    def remove_collision_label(self, label: str) -> None:
        properties = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            key=label,
        )
        coords = self.check_collision_zones(
            self._map_manager.collision_map, label
        )
        if coords:
            for coord in coords:
                self._map_manager.collision_map[coord] = properties

    def get_collision_map(self) -> CollisionMap:
        """
        Return dictionary for collision testing.

        Returns a dictionary where keys are (x, y) tile tuples
        and the values are tiles or NPCs.

        # NOTE:
        This will not respect map changes to collisions
        after the map has been loaded!

        Returns:
            A dictionary of collision tiles.
        """
        collision_dict: DefaultDict[
            tuple[int, int], Optional[RegionProperties]
        ] = defaultdict(lambda: RegionProperties([], [], [], None, None))

        # Get all the NPCs' tile positions
        for npc in self._npc_manager.get_all_entities():
            collision_dict[npc.tile_pos] = self._get_region_properties(
                npc.tile_pos, npc
            )

        # Add surface map entries to the collision dictionary
        for coords, surface in self._map_manager.surface_map.items():
            for label, value in surface.items():
                if float(value) == 0:
                    collision_dict[coords] = self._get_region_properties(
                        coords, label
                    )

        collision_dict.update(
            {k: v for k, v in self._map_manager.collision_map.items()}
        )

        return dict(collision_dict)

    def _get_region_properties(
        self, coords: tuple[int, int], entity_or_label: Union[NPC, str]
    ) -> RegionProperties:
        """
        Constructs a RegionProperties object for the given tile coordinates,
        using either an NPC entity or a string label.

        Parameters:
            coords: The (x, y) tile position.
            entity_or_label: Either an NPC or a label string.

        Returns:
            A RegionProperties object representing the collision state.
        """
        region: Optional[RegionProperties] = (
            self._map_manager.collision_map.get(coords)
        )

        enter_from = region.enter_from if region else []
        exit_from = region.exit_from if region else []
        endure = region.endure if region else []
        push_effect = region.push_effect if region else None
        speed_modifier = region.speed_modifier if region else None
        key = region.key if region else None

        if isinstance(entity_or_label, str):
            return RegionProperties(
                enter_from=enter_from,
                exit_from=exit_from,
                endure=endure,
                key=entity_or_label,
                push_effect=push_effect,
                speed_modifier=speed_modifier,
            )
        else:
            return RegionProperties(
                enter_from=enter_from,
                exit_from=exit_from,
                endure=endure,
                entity=entity_or_label,
                key=key,
                push_effect=push_effect,
                speed_modifier=speed_modifier,
            )
