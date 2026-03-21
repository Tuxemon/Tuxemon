# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.network.client import TuxemonClient
from tuxemon.network.server import TuxemonServer

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.db import Direction
    from tuxemon.entity.entity import Entity


class NetworkManager:
    def __init__(self, parent: BaseClient) -> None:
        self.parent = parent
        self.event_bus = parent.event_bus
        self.server: TuxemonServer | None = None
        self.client: TuxemonClient | None = None
        self._last_host_state = False
        self._last_client_state = False

    def initialize(self) -> None:
        if self.server or self.client:
            logger.error(
                "NetworkManager: Already initialized, cannot reinitialize."
            )
            raise RuntimeError("NetworkManager is already initialized.")

        self.server = TuxemonServer(self.parent)
        self.client = TuxemonClient(self.parent)
        self.event_bus.subscribe("entity_move_start", self._on_move_start)
        self.event_bus.subscribe("entity_move_stop", self._on_move_stop)
        self.event_bus.subscribe("entity_tile_change", self._on_tile_change)

    def update(self, dt: float) -> None:
        if self.client and self.client.listening:
            self.client.update()
            current_map = self.parent.get_map_name()
            self.parent.npc_manager.add_clients_to_map(
                self.client.registry, current_map
            )

        if self.server and self.server.listening:
            self.server.update()

        new_host_state = self.is_host()
        new_client_state = self.is_client()

        if new_host_state != self._last_host_state:
            logger.info(
                f"Host state changed: {self._last_host_state} -> {new_host_state}"
            )
            self._last_host_state = new_host_state

        if new_client_state != self._last_client_state:
            logger.info(
                f"Client state changed: {self._last_client_state} -> {new_client_state}"
            )
            self._last_client_state = new_client_state

    def shutdown(self) -> None:
        """
        Gracefully stops all network operations (server and client).
        """
        self.event_bus.unsubscribe("entity_move_start", self._on_move_start)
        self.event_bus.unsubscribe("entity_move_stop", self._on_move_stop)
        self.event_bus.unsubscribe("entity_tile_change", self._on_tile_change)

        if self.server and self.server.listening:
            self.server.shutdown()
            logger.info("NetworkManager: Server shutdown complete.")
        self.server = None

        if self.client and self.client.listening:
            self.client.disconnect()
            logger.info("NetworkManager: Client disconnected.")
        self.client = None

        logger.info("NetworkManager: All networking systems shut down.")

    def is_host(self) -> bool:
        return self.server is not None and self.server.listening

    def is_client(self) -> bool:
        return self.client is not None and self.client.listening

    def is_connected(self) -> bool:
        return self.is_host() or self.is_client()

    def _on_move_start(self, entity: Entity, direction: Direction) -> None:
        if self.is_client() and entity.is_player and self.client:
            self.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def _on_move_stop(self, entity: Entity) -> None:
        if self.is_client() and entity.is_player and self.client:
            self.client.update_player(
                entity.facing,
                event_type="CLIENT_MOVE_COMPLETE",
            )

    def _on_tile_change(self, entity: Entity, pos: tuple[int, int]) -> None:
        if self.is_client() and entity.is_player and self.client:
            self.client.update_player(
                entity.facing,
                event_type="CLIENT_LOCATION_SYNC",
                position=pos,
            )
