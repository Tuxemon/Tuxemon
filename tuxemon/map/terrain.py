# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.platform.const.sizes import SURFACE_KEYS

if TYPE_CHECKING:
    from tuxemon.map.manager import MapManager


class TerrainManager:
    """Manages terrain-related tile properties in the surface map."""

    def __init__(self, map_manager: MapManager):
        self.map_manager = map_manager

    def get_all_tile_properties(
        self,
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Return all tile coordinates that contain the given surface label.
        """
        return [
            coords
            for coords, props in self.map_manager.surface_map.items()
            if label in props
        ]

    def update_tile_property(self, label: str, moverate: float) -> None:
        """
        Update the moverate for all tiles that already contain `label`.

        This preserves the original guarantee:
        - no new dictionary entries are created
        - only existing keys are updated
        - invalid labels (not in SURFACE_KEYS) are ignored
        """
        if label not in SURFACE_KEYS:
            return

        for coord in self.get_all_tile_properties(label):
            props = self.map_manager.surface_map.get(coord)
            if props and props.get(label) != moverate:
                props[label] = moverate

    def all_tiles_modified(self, label: str, moverate: float) -> bool:
        """
        Check whether all tiles containing `label` have the expected moverate.
        """
        return all(
            self.map_manager.surface_map[coord].get(label) == moverate
            for coord in self.get_all_tile_properties(label)
        )
