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


class NetworkManager:
    def __init__(self, parent: BaseClient) -> None:
        self.parent = parent
        self.server: TuxemonServer | None = None
        self.client: TuxemonClient | None = None
        self._last_host_state = False
        self._last_client_state = False

    def initialize(self) -> None:
        if self.server or self.client:
            logger.warning("NetworkManager: Already initialized.")
            return
        self.server = TuxemonServer(self.parent)
        self.client = TuxemonClient(self.parent)

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
        if self.server and self.server.listening:
            self.server.shutdown()
            self.server = None
            logger.info("NetworkManager: Server shutdown complete.")

        if self.client and self.client.listening:
            self.client.disconnect()
            self.client = None
            logger.info("NetworkManager: Client disconnected.")

        self.server = None
        self.client = None
        logger.info("NetworkManager: All networking systems shut down.")

    def is_host(self) -> bool:
        return self.server is not None and self.server.listening

    def is_client(self) -> bool:
        return self.client is not None and self.client.listening

    def is_connected(self) -> bool:
        return self.is_host() or self.is_client()
