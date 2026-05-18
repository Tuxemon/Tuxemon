# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime
from queue import Empty, Queue
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import websockets
from websockets.asyncio.server import ServerConnection

from tuxemon.network.networking import EventType

if TYPE_CHECKING:
    from tuxemon.network.controller import ServerInterface

logger = logging.getLogger(__name__)


class WebsocketServerWrapper:
    def __init__(self, game_server: ServerInterface) -> None:
        self.game_server = game_server
        self.incoming_queue: Queue[tuple[str, dict[str, Any]]] = Queue()
        self.client_registry: dict[str, ServerConnection] = {}
        self.registry: dict[str, dict[str, Any]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None
        self.net_thread: threading.Thread | None = None
        self.loop_ready = threading.Event()
        self.heartbeat_interval = 20  # Seconds between pings
        self.heartbeat_timeout = 10  # Seconds to wait for pong
        self.max_clients: int | None = None
        self.debug: bool = False

    def start_listening(self, port: int) -> None:
        """Starts the network thread and the asynchronous server."""
        self.net_thread = threading.Thread(
            target=self._run_async_loop, args=("0.0.0.0", port), daemon=True
        )
        self.net_thread.start()
        self.loop_ready.wait()

    def stop_listening(self) -> None:
        """Stops the server loop and disconnects all active clients."""
        if not self.loop or not self.loop.is_running():
            return

        logger.info("Initiating server shutdown...")

        assert self.loop is not None
        future = asyncio.run_coroutine_threadsafe(
            self._internal_shutdown(), self.loop
        )

        try:
            future.result(timeout=5)
        except Exception as e:
            logger.error(f"Error during async shutdown: {e}")

        if self.net_thread:
            self.net_thread.join(timeout=1)

    def get_incoming_events(self) -> list[tuple[str, dict[str, Any]]]:
        """Called by TuxemonServer.update() to pull all new client messages."""
        events: list[tuple[str, dict[str, Any]]] = []
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

        assert self.loop is not None, "Event loop not initialized"

        websocket = self.client_registry.get(cuuid)
        if websocket:
            asyncio.run_coroutine_threadsafe(
                websocket.send(json_data), self.loop
            )

    def notify_broadcast(self, exclude_cuuid: str, json_data: str) -> None:
        """Sends pre-serialized JSON to everyone except the originator."""
        assert self.loop is not None, "Event loop not initialized"

        for cuuid, websocket in self.client_registry.items():
            if cuuid != exclude_cuuid:
                asyncio.run_coroutine_threadsafe(
                    websocket.send(json_data), self.loop
                )

    def disconnect_client(self, cuuid: str) -> None:
        if self.loop is None:
            self.client_registry.pop(cuuid, None)
            return

        websocket = self.client_registry.pop(cuuid, None)
        if websocket:
            close_result = websocket.close()
            if asyncio.iscoroutine(close_result):
                asyncio.run_coroutine_threadsafe(close_result, self.loop)
            else:
                websocket.close()

    def _run_async_loop(self, host: str, port: int) -> None:
        """Entry point for the network thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop_ready.set()

        async def start() -> None:
            async with websockets.serve(
                self._handler,
                host,
                port,
                ping_interval=self.heartbeat_interval,
                ping_timeout=self.heartbeat_timeout,
            ) as server:
                logger.info(
                    f"WebSocket server started on {host}:{port} with heartbeats."
                )
                await server.wait_closed()

        self.loop.run_until_complete(start())

    async def _handler(self, websocket: ServerConnection) -> None:
        cuuid = None
        reason = "connection_closed"
        try:
            first_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(first_msg)

            peer = websocket.remote_address
            peer_str = f"{peer[0]}:{peer[1]}" if peer else "unknown"

            if (
                self.max_clients is not None
                and len(self.client_registry) >= self.max_clients
            ):
                logger.warning(
                    f"Rejecting new connection from {peer_str}: server full"
                )
                await websocket.close(code=4000, reason="Server full")
                return

            provided_cuuid = data.get("cuuid")
            if provided_cuuid and provided_cuuid in self.registry:
                cuuid = provided_cuuid
                logger.info(f"Client {cuuid} reconnected from {peer_str}.")
            else:
                cuuid = str(uuid4())
                self.registry[cuuid] = {
                    "peer": peer_str,
                    "connected_at": datetime.now(),
                    "last_message_at": datetime.now(),
                }
                logger.info(f"New client {cuuid} connected from {peer_str}.")

            self.client_registry[cuuid] = websocket
            self.incoming_queue.put((cuuid, data))

            await self._listen_to_client(cuuid, websocket)

        except StopAsyncIteration:
            # Normal end of async iterator
            pass

        except Exception as e:
            logger.error(f"Handshake failed: {e}")
            reason = "handshake_failed"
            cuuid = cuuid or str(uuid4())
            self._handle_disconnect(cuuid, reason=reason)
        finally:
            closed = getattr(websocket, "closed", False)
            if cuuid is not None and isinstance(closed, bool) and closed:
                self._handle_disconnect(cuuid, reason=reason)

    async def _listen_to_client(
        self, cuuid: str, websocket: ServerConnection
    ) -> None:
        """Receives messages from a single connected client."""
        try:
            async for message in websocket:
                if self.debug:
                    logger.debug(f"Raw incoming from {cuuid}: {message!r}")

                try:
                    event_data = json.loads(message)
                    if not self._is_valid_event(event_data):
                        logger.warning(
                            f"Invalid event payload from {cuuid}: {event_data}"
                        )
                        continue
                    if cuuid in self.registry:
                        self.registry[cuuid]["last_message_at"] = (
                            datetime.now()
                        )
                    self.incoming_queue.put((cuuid, event_data))
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {cuuid}")
        except asyncio.CancelledError:
            logger.info(f"Listener cancelled for {cuuid}")
        except Exception as e:
            logger.error(f"Error in client listener for {cuuid}: {e}")

    def _is_valid_event(self, payload: dict[str, Any]) -> bool:
        if "type" not in payload:
            return False
        if not isinstance(payload["type"], str):
            return False
        return True

    def _handle_disconnect(self, cuuid: str, reason: str = "unknown") -> None:
        """Cleans up the registry and notifies the game thread."""
        peer = self.registry.get(cuuid, {}).get("peer", "unknown")
        logger.info(
            f"Client {cuuid} disconnected from {peer}, reason={reason}"
        )

        self.client_registry.pop(cuuid, None)
        self.registry.pop(cuuid, None)

        disconnect_event = {
            "type": EventType.CLIENT_DISCONNECTED.value,
            "event_number": self.game_server.get_next_event_number(),
            "cuuid": cuuid,
            "is_temporary": True,
            "reason": reason,
        }
        self.incoming_queue.put((cuuid, disconnect_event))

    async def _internal_shutdown(self) -> None:
        """Closes all connections and stops the loop (runs inside async thread)."""
        logger.info("Shutting down WebSocket connections...")
        close_tasks = [ws.close() for ws in self.client_registry.values()]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self.client_registry.clear()
        self.registry.clear()

        assert self.loop is not None, "Event loop not initialized"
        self.loop.stop()
