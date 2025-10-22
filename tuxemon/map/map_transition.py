# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.boundary import BoundaryChecker
    from tuxemon.event.eventengine import EventEngine
    from tuxemon.map.map_loader import MapLoader
    from tuxemon.map.map_manager import MapManager
    from tuxemon.map.map_tuxemon import TuxemonMap
    from tuxemon.npc_manager import NPCManager

logger = logging.getLogger(__name__)


class MapTransition:
    """Handles transitioning between maps, updating game state accordingly."""

    def __init__(
        self,
        map_loader: MapLoader,
        npc_manager: NPCManager,
        map_manager: MapManager,
        boundary: BoundaryChecker,
        event_engine: EventEngine,
    ) -> None:
        self.map_loader = map_loader
        self.map_manager = map_manager
        self.npc_manager = npc_manager
        self.boundary = boundary
        self.event_engine = event_engine

    def change_map(self, map_name: str) -> None:
        """
        Loads the new map and updates relevant game components.

        Parameters:
            map_name: The name of the new map.
        """
        logger.debug(f"Loading map '{map_name}' using Client's MapLoader.")
        self._clear_npcs()

        map_data = self.map_loader.load_map_data(map_name)

        self._reset_events(map_data)
        self._update_map_state(map_data)
        self._update_boundaries()

    def _reset_events(self, map_data: TuxemonMap) -> None:
        """Resets and updates event engine for the new map."""
        self.event_engine.reset()
        self.event_engine.set_current_map(map_data)

    def _update_map_state(self, map_data: TuxemonMap) -> None:
        """Updates the map manager with new map data."""
        self.map_manager.load_map(map_data)

    def _clear_npcs(self) -> None:
        """Clears NPCs to ensure a clean transition."""
        self.npc_manager.clear_npcs()

    def _update_boundaries(self) -> None:
        """Updates the game boundaries to fit the new map."""
        map_size = self.map_manager.map_size
        self.boundary.set_rectangular_boundary(
            "map", 0, map_size[0], 0, map_size[1]
        )
