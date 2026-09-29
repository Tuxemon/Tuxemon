# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Tuxemon server and client."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

from tuxemon.network.networking import EventType
from tuxemon.network.websocket_server import WebsocketServerWrapper
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


logger = logging.getLogger(__name__)


class ServerInterface(Protocol):
    def get_next_event_number(self) -> int: ...


class WebsocketSControllerWrapper(ServerInterface):
    """
    Wrapper around WebsocketServerWrapper to handle controller-specific networking.
    """

    def __init__(self, controller_server: ControllerServer, port: int) -> None:
        self.controller_server = controller_server
        self.server = WebsocketServerWrapper(self)
        self.port = port

    def start_listening(self) -> None:
        """Starts the underlying WebSocket server."""
        self.server.start_listening(self.port)

    def get_incoming_events(
        self,
    ) -> Sequence[tuple[str, str | dict[str, Any]]]:
        """Returns all incoming controller events."""
        return self.server.get_incoming_events()

    def get_next_event_number(self) -> int:
        return self.controller_server.get_next_event_number()


class ControllerServer:
    """
    Server class for a networked controller, using a thread-safe WebSockets wrapper.

    The wrapper handles asynchronous network events and passes them
    to the local game for processing via a queue.
    """

    def __init__(self, game: BaseClient) -> None:
        """
        Initializes the ControllerServer instance.
        """
        self.game = game
        self.listening = False
        self.interfaces: dict[str, Any] = {}

        controller_port = 40082
        self._event_counter = 0

        self.server = WebsocketSControllerWrapper(self, controller_port)
        self.server.start_listening()
        self.listening = True

    def update(self) -> None:
        """Updates the server state by pulling events from the network wrapper."""
        controller_events = self.net_controller_loop()
        if controller_events:
            key_events_buffer = list(self.game.key_events)

            for controller_event in controller_events:
                key_events_buffer.append(controller_event)
                if self.game.current_state:
                    self.game.current_state.process_event(controller_event)

            self.game.key_events = tuple(key_events_buffer)

    def get_next_event_number(self) -> int:
        self._event_counter += 1
        return self._event_counter

    def net_controller_loop(self) -> Sequence[PlayerInput]:
        event_map = {
            "KEYDOWN:up": PlayerInput(button=buttons.UP, value=1),
            "KEYUP:up": PlayerInput(button=buttons.UP, value=0),
            "KEYDOWN:down": PlayerInput(button=buttons.DOWN, value=1),
            "KEYUP:down": PlayerInput(button=buttons.DOWN, value=0),
            "KEYDOWN:left": PlayerInput(button=buttons.LEFT, value=1),
            "KEYUP:left": PlayerInput(button=buttons.LEFT, value=0),
            "KEYDOWN:right": PlayerInput(button=buttons.RIGHT, value=1),
            "KEYUP:right": PlayerInput(button=buttons.RIGHT, value=0),
            "KEYDOWN:enter": PlayerInput(button=buttons.A, value=1),
            "KEYUP:enter": PlayerInput(button=buttons.A, value=0),
            "KEYDOWN:esc": PlayerInput(button=buttons.BACK, value=1),
            "KEYUP:esc": PlayerInput(button=buttons.BACK, value=0),
        }

        events: list[PlayerInput] = []

        for cuuid, raw_payload in self.server.get_incoming_events():
            try:
                if isinstance(raw_payload, str):
                    payload_dict = json.loads(raw_payload)
                else:
                    payload_dict = raw_payload

                event_data_key = payload_dict.get("type", "")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from controller: {raw_payload}")
                continue

            if event_data_key == EventType.CLIENT_DISCONNECTED.value:
                logger.info(f"Controller {cuuid} disconnected")
                continue

            event = event_map.get(event_data_key)
            if event:
                events.append(event)
            else:
                logger.warning(f"Unknown network event: {event_data_key}")

        return events
