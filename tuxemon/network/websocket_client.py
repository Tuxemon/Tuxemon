# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import json
import logging
import threading
from queue import Empty, Queue
from typing import Any, cast

import websockets
from websockets.legacy.protocol import WebSocketCommonProtocol

logger = logging.getLogger(__name__)


class WebsocketClientWrapper:
    def __init__(self, port: int) -> None:
        self.port = port
        self.send_queue: Queue[str] = Queue()
        self.receive_queue: Queue[dict[str, Any]] = Queue()
        self.running = threading.Event()
        self.registered: bool = False
        self.registry: dict[str, Any] = {}

    def start_connection(self, ip: str, port: int) -> None:
        """Starts the network thread and asyncio loop."""
        if not self.running.is_set():
            self.running.set()
            self.net_thread = threading.Thread(
                target=self._run_async_loop, args=(ip, port), daemon=True
            )
            self.net_thread.start()

    def disconnect(self) -> None:
        """Stops the network thread and closes the connection."""
        if self.running.is_set():
            self.running.clear()
            self.registered = False
            logger.info("Client manually disconnected.")

    def is_connected(self) -> bool:
        return self.registered and self.running.is_set()

    def send(self, json_data: str) -> None:
        """Called by TuxemonClient to send a message."""
        try:
            self.send_queue.put_nowait(json_data)
        except Exception as e:
            logger.error(f"Send queue error: {e}")

    def event(self, data: dict[str, Any]) -> None:
        try:
            json_data = json.dumps(data)
            self.send(json_data)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize event: {e}")

    def get_incoming_events(self) -> list[dict[str, Any]]:
        """Called by TuxemonClient.update() to pull all new server messages."""
        events = []
        while True:
            try:
                events.append(self.receive_queue.get_nowait())
            except Empty:
                break
        return events

    def _run_async_loop(self, ip: str, port: int) -> None:
        """Entry point for the network thread."""
        logger.info("Network thread started.")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.loop.run_until_complete(self._connect_and_listen(ip, port))

    async def _connect_and_listen(self, ip: str, port: int) -> None:
        uri = f"ws://{ip}:{port}"
        try:
            async with websockets.connect(uri) as raw_websocket:
                websocket = cast(WebSocketCommonProtocol, raw_websocket)
                logger.info(f"Connected to {uri}!")
                self.registered = True
                receive_task = self.loop.create_task(
                    self._receive_loop(websocket)
                )
                send_task = self.loop.create_task(self._send_loop(websocket))

                await asyncio.gather(receive_task, send_task)

        except ConnectionRefusedError:
            logger.error("Connection refused.")
        finally:
            self.running.clear()
            logger.info("Connection closed.")

    async def _receive_loop(self, websocket: WebSocketCommonProtocol) -> None:
        """Continuously listens for messages from the server."""
        while self.running.is_set():
            try:
                message = await websocket.recv()
                self.receive_queue.put(json.loads(message))
            except websockets.exceptions.ConnectionClosedOK:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break

    async def _send_loop(self, websocket: WebSocketCommonProtocol) -> None:
        """Continuously checks the send queue and transmits data."""
        while self.running.is_set():
            try:
                message = await asyncio.to_thread(
                    self.send_queue.get, timeout=0.1
                )
                await websocket.send(message)
            except Empty:
                pass
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Send error: {e}")
                break
