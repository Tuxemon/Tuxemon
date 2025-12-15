# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tuxemon.network.client import TuxemonClient
from tuxemon.network.networking import ConnectionState
from tuxemon.network.server import TuxemonServer

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class NetworkManager:
    def __init__(self, parent: BaseClient) -> None:
        self.parent = parent
        self.server: Optional[TuxemonServer] = None
        self.client: Optional[TuxemonClient] = None
        self._state = ConnectionState.DISCONNECTED

    @property
    def state(self) -> ConnectionState:
        """Returns the current connection state."""
        return self._state

    def set_state(self, new_state: ConnectionState) -> None:
        """Sets the connection state and logs the change if different."""
        if new_state != self._state:
            self._state = new_state
            self._log_connection_state()

    def initialize(self) -> None:
        if self.server or self.client:
            logger.warning("NetworkManager: Already initialized.")
            return
        self.server = TuxemonServer(self.parent)
        self.client = TuxemonClient(self.parent)

    def update(self, time_delta: float) -> None:
        if self.client and self.client.listening:
            self.client.update(time_delta)
            current_map = self.parent.get_map_name()
            self.parent.npc_manager.add_clients_to_map(
                self.client.registry, current_map
            )

        if self.server and self.server.listening:
            self.server.update()

        new_state = self._determine_connection_state()

        # Update state and log changes
        if new_state != self._state:
            self._state = new_state
            self._log_connection_state()

    def _determine_connection_state(self) -> ConnectionState:
        if self.server and self.server.listening:
            return ConnectionState.HOST
        elif self.client and self.client.listening:
            return ConnectionState.CLIENT
        return ConnectionState.DISCONNECTED

    def _log_connection_state(self) -> None:
        if self._state == ConnectionState.HOST:
            logger.info("NetworkManager: Host connection just established")
        elif self._state == ConnectionState.CLIENT:
            logger.info("NetworkManager: Client connection just established")
        elif self._state == ConnectionState.DISCONNECTED:
            logger.info("NetworkManager: All connections lost")

    def is_host(self) -> bool:
        return self._state == ConnectionState.HOST

    def is_client(self) -> bool:
        return self._state == ConnectionState.CLIENT

    def is_connected(self) -> bool:
        return self._state in {
            ConnectionState.HOST,
            ConnectionState.CLIENT,
        }
