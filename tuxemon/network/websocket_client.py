# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import json
import logging
import threading
from enum import Enum, auto
from queue import Empty, Queue
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    REGISTERING = auto()
    REGISTERED = auto()
    READY = auto()


class WebsocketClientWrapper:
    """
    Thread-based sync façade over an asyncio websockets client.

    Responsibilities:
      - Own the asyncio event loop in a dedicated thread.
      - Maintain connection state.
      - Handle JSON serialization/deserialization.
      - Provide thread-safe send + receive queues.
      - Optionally send periodic pings to keep the connection alive.
    """

    def __init__(
        self,
        port: int,
        ping_interval: float = 2.0,
    ) -> None:
        self.port = port

        self._send_queue: Queue[str] = Queue()
        self._receive_queue: Queue[dict[str, Any]] = Queue()

        self._running = threading.Event()
        self._registered: bool = False
        self._state: ConnectionState = ConnectionState.DISCONNECTED

        self.registry: dict[str, Any] = {}

        self._loop: asyncio.AbstractEventLoop | None = None
        self._net_thread: threading.Thread | None = None

        self._ip: str | None = None
        self._port: int | None = None

        self._ping_interval = ping_interval

    @property
    def registered(self) -> bool:
        return self._registered

    @property
    def running(self) -> bool:
        return self._running.is_set()

    @property
    def state(self) -> ConnectionState:
        return self._state

    def start_connection(self, ip: str, port: int | None = None) -> None:
        """
        Starts the network thread and asyncio loop and attempts to connect
        to the given IP/port.
        """
        if self._running.is_set():
            self._ip = ip
            self._port = port if port is not None else self.port
            self._schedule_connect()
            return

        self._ip = ip
        self._port = port if port is not None else self.port

        self._running.set()
        self._net_thread = threading.Thread(
            target=self._run_loop_thread,
            daemon=True,
        )
        self._net_thread.start()

    def disconnect(self) -> None:
        """Stops the network thread and closes the connection."""
        if not self._running.is_set():
            return

        logger.info("Client manually disconnecting...")
        self._running.clear()
        self._registered = False
        self._set_state(ConnectionState.DISCONNECTED)

        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)

    def is_connected(self) -> bool:
        """Returns True if the client is logically connected and running."""
        return self._registered and self._running.is_set()

    def send_event(self, data: dict[str, Any]) -> None:
        """
        Public API: enqueue a Python dict as a JSON message to be sent.
        """
        try:
            json_data = json.dumps(data)
            self._send(json_data)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize event: {e}")

    def get_incoming_events(self) -> list[dict[str, Any]]:
        """
        Public API: pull all new server messages as Python dicts.
        Intended to be called from the main thread/game loop.
        """
        events: list[dict[str, Any]] = []
        while True:
            try:
                events.append(self._receive_queue.get_nowait())
            except Empty:
                break
        return events

    def _send(self, json_data: str) -> None:
        """Low-level: enqueue raw JSON string for sending."""
        try:
            self._send_queue.put_nowait(json_data)
        except Exception as e:
            logger.error(f"Send queue error: {e}")

    def _set_state(self, new_state: ConnectionState) -> None:
        if self._state == new_state:
            return
        logger.info(f"Connection state: {self._state} -> {new_state}")
        self._state = new_state

    def _schedule_connect(self) -> None:
        loop = self._loop
        if loop is not None and loop.is_running() and self._ip and self._port:
            loop.call_soon_threadsafe(
                loop.create_task,
                self._connect_and_listen(self._ip, self._port),
            )

    def _run_loop_thread(self) -> None:
        """
        Entry point for the network thread.

        Creates and owns the asyncio event loop, runs it forever, and
        manages connection tasks inside the loop.
        """
        logger.info("Network thread started.")
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)

        if self._ip and self._port:
            loop.create_task(self._connect_and_listen(self._ip, self._port))

        try:
            loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            pending = {t for t in asyncio.all_tasks(loop) if not t.done()}
            for task in pending:
                task.cancel()
            if pending:
                try:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                except Exception:
                    pass

            loop.close()
            self._loop = None
            self._running.clear()
            self._registered = False
            self._set_state(ConnectionState.DISCONNECTED)
            logger.info("Network thread stopped; event loop closed.")

    async def _connect_and_listen(self, ip: str, port: int) -> None:
        """
        Single connection lifecycle.

        Establishes the websocket, then runs send/receive and ping loops
        until the connection drops or the client is stopped.
        """
        if not self._running.is_set():
            return

        uri = f"ws://{ip}:{port}"
        self._set_state(ConnectionState.CONNECTING)
        logger.info(f"Attempting connection to {uri}...")

        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to {uri}!")
                self._set_state(ConnectionState.CONNECTED)
                self._registered = True

                receive_task = asyncio.create_task(
                    self._receive_loop(websocket)
                )
                send_task = asyncio.create_task(self._send_loop(websocket))
                ping_task = asyncio.create_task(self._ping_loop(websocket))

                done, pending = await asyncio.wait(
                    {receive_task, send_task, ping_task},
                    return_when=asyncio.FIRST_EXCEPTION,
                )

                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)

        except ConnectionRefusedError:
            logger.error("Connection refused.")
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
        finally:
            self._registered = False
            self._set_state(ConnectionState.DISCONNECTED)
            logger.info("Connection closed.")

    async def _receive_loop(self, websocket: ClientConnection) -> None:
        """Continuously listens for messages from the server."""
        while self._running.is_set():
            try:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                except (TypeError, ValueError) as e:
                    logger.error(f"Failed to decode incoming message: {e}")
                    continue
                self._receive_queue.put(data)
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("Websocket closed normally by server.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(f"Websocket closed with error: {e}")
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break

    async def _send_loop(self, websocket: ClientConnection) -> None:
        """
        Continuously checks the send_queue and transmits data.

        Uses non-blocking get_nowait() on the thread-safe Queue to avoid
        blocking the event loop; falls back to a short sleep when empty.
        """
        while self._running.is_set():
            try:
                message = self._send_queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
                continue

            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("Websocket closed while sending.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(f"Websocket send failed, connection closed: {e}")
                break
            except Exception as e:
                logger.error(f"Send error: {e}")
                break

    async def _ping_loop(self, websocket: ClientConnection) -> None:
        """Periodically sends a ping event to keep the connection alive."""
        while self._running.is_set() and self._ping_interval > 0:
            await asyncio.sleep(self._ping_interval)
            try:
                ping_event = {"type": "PING"}
                await websocket.send(json.dumps(ping_event))
            except websockets.exceptions.ConnectionClosed:
                logger.info("Ping loop stopped: websocket closed.")
                break
            except Exception as e:
                logger.error(f"Ping error: {e}")
                break
