# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import json
import logging
import threading
from queue import Empty, Queue
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from tuxemon.network.networking import EventType

if TYPE_CHECKING:
    from tuxemon.network.controller import ServerInterface

logger = logging.getLogger(__name__)


class WebsocketServerWrapper:
    def __init__(self, game_server: ServerInterface) -> None:
        self.game_server = game_server
        self.incoming_queue: Queue[tuple[str, dict[str, Any]]] = Queue()
        self.client_registry: dict[str, WebSocketServerProtocol] = {}
        self.registry: dict[str, dict[str, Any]] = {}

    def start_listening(self, port: int) -> None:
        """Starts the network thread and the asynchronous server."""
        self.net_thread = threading.Thread(
            target=self._run_async_loop, args=("0.0.0.0", port), daemon=True
        )
        self.net_thread.start()

    def get_incoming_events(self) -> list[tuple[str, dict[str, Any]]]:
        """Called by TuxemonServer.update() to pull all new client messages."""
        events = []
        while True:
            try:
                events.append(self.incoming_queue.get_nowait())
            except Empty:
                break
        return events

    def notify(self, cuuid: str, json_data: str) -> None:
        """Sends a message to a single client."""
        if cuuid is None:
            logger.warning("Cannot notify: cuuid is None")
            return
        websocket = self.client_registry.get(cuuid)
        if websocket:
            asyncio.run_coroutine_threadsafe(
                websocket.send(json_data), self.loop
            )

    def disconnect_client(self, cuuid: str) -> None:
        websocket = self.client_registry.pop(cuuid, None)
        self.registry.pop(cuuid, None)
        if websocket:
            asyncio.run_coroutine_threadsafe(websocket.close(), self.loop)

    def _run_async_loop(self, host: str, port: int) -> None:
        """Entry point for the network thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def start() -> None:
            server = await websockets.serve(self._handler, host, port)  # type: ignore[arg-type]
            logger.info(f"WebSocket server started on {host}:{port}")
            await server.wait_closed()

        self.loop.run_until_complete(start())

    async def _handler(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handles a single new client connection."""
        cuuid = str(uuid4())
        self.client_registry[cuuid] = websocket
        self.registry[cuuid] = {}

        logger.info(f"Client {cuuid} connected.")

        try:
            await self._listen_to_client(cuuid, websocket)

        except Exception as e:
            logger.error(f"Client {cuuid} error: {e}")
        finally:
            logger.info(f"Client {cuuid} disconnected.")
            self._handle_disconnect(cuuid)

    async def _listen_to_client(
        self, cuuid: str, websocket: WebSocketServerProtocol
    ) -> None:
        """Receives messages from a single connected client."""
        async for message in websocket:
            try:
                event_data = json.loads(message)
                self.incoming_queue.put((cuuid, event_data))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {cuuid}")

    def _handle_disconnect(self, cuuid: str) -> None:
        """Cleans up the registry and notifies the game thread."""
        self.client_registry.pop(cuuid, None)

        disconnect_event = {
            "type": EventType.CLIENT_DISCONNECTED.value,
            "event_number": self.game_server.get_next_event_number(),
            "cuuid": cuuid,
        }
        self.incoming_queue.put((cuuid, disconnect_event))
