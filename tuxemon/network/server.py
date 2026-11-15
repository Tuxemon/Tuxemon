# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import datetime
from itertools import count
from typing import TYPE_CHECKING, Any

from tuxemon.db import Direction
from tuxemon.network.networking import CharData, EventData, EventType
from tuxemon.network.websocket_server import WebsocketServerWrapper

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


SERVER_NAME = "Default Tuxemon Server"


class TuxemonServer:
    """
    Server class for managing multiplayer game state and communication using
    WebSockets.
    """

    def __init__(
        self,
        game: BaseClient,
        server_name: str | None = SERVER_NAME,
        server_port: int = 40081,
        timeout: int = 15,
    ) -> None:
        """
        Initializes the TuxemonServer instance, sets up networking, event routing,
        and client state management.
        """
        self.timeout = timeout
        self.game = game
        self.server_name = server_name
        self.server_port = server_port
        self.network_events: list[str] = []
        self.listening = False
        self.interfaces: dict[str, Any] = {}
        self.ips: list[str] = []
        self._event_counter = count(start=1)
        self.server_timestamp: datetime = datetime.now()

        self.server = WebsocketServerWrapper(self)
        self.server.max_clients = 32
        self.server.start_listening(self.server_port)
        self.listening = True
        self.client_registry = ClientRegistry(timeout=self.timeout)
        self.event_router = EventRouter(
            self.client_registry.registry, self.get_next_event_number
        )
        self.event_factory = EventFactory(self.get_next_event_number)
        self.notification_manager = NotificationManager(
            self.server,
            self.get_next_event_number,
            self.event_factory,
            self.client_registry,
        )
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """
        Registers all event handlers with the event router for dispatching
        incoming events to appropriate methods.
        """
        self.event_router.register_handler(
            EventType.PUSH_SELF, self.handle_push_self_event
        )
        self.event_router.register_handler(
            EventType.PING, self.handle_ping_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_INTERACTION, self.handle_client_interaction_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_RESPONSE, self.handle_client_response_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_KEYDOWN,
            lambda c, e: self.handle_key_event(c, e, True),
        )
        self.event_router.register_handler(
            EventType.CLIENT_KEYUP,
            lambda c, e: self.handle_key_event(c, e, False),
        )
        self.event_router.register_handler(
            EventType.CLIENT_START_BATTLE, self.handle_start_battle_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_DISCONNECTED,
            self.handle_client_disconnected_event,
        )

    def shutdown(self) -> None:
        """
        Gracefully stops the server: closes the listening socket and
        disconnects all active clients.
        """
        shutdown_event = self.event_factory.create_event(
            EventType.SERVER_SHUTDOWN,
            cuuid="SERVER",
        )

        for cuuid in list(self.client_registry.registry.keys()):
            self.notify_client(cuuid, shutdown_event)

        for cuuid in list(self.client_registry.registry.keys()):
            self.server.disconnect_client(cuuid)
            event_data = self.event_factory.create_event(
                EventType.CLIENT_DISCONNECTED, cuuid
            )
            self.notify_client(cuuid, event_data)

        self.client_registry.registry.clear()
        self.listening = False
        logger.info(
            "TuxemonServer: Shutdown complete. Server is no longer listening."
        )

    def get_next_event_number(self) -> int:
        """
        Generates and returns the next unique event number using itertools.
        """
        return next(self._event_counter)

    def update(self) -> None:
        self.server_timestamp = datetime.now()

        incoming = self.server.get_incoming_events()
        for cuuid, event_dict in incoming:
            try:
                event_data = EventData.from_dict(event_dict)
                self.server_event_handler(cuuid, event_data)
            except Exception:
                logger.exception(f"Critical error handling event from {cuuid}")

        timed_out = self.client_registry.check_timeouts(self.server_timestamp)
        for cuuid in timed_out:
            self._handle_timeout_disconnection(cuuid)

    def _handle_timeout_disconnection(self, cuuid: str) -> None:
        """Internal helper to clean up a timed-out client."""
        logger.info(f"Client Timeout: {cuuid}")
        event_data = self.event_factory.create_event(
            EventType.CLIENT_DISCONNECTED, cuuid
        )
        self.notify_client(cuuid, event_data)
        self.server.disconnect_client(cuuid)
        self.client_registry.remove_client(cuuid)

    def server_event_handler(self, cuuid: str, event_data: EventData) -> None:
        """
        Delegates an incoming event to the appropriate handler via the
        event router.
        """
        self.event_router.route_event(cuuid, event_data)

    def handle_client_disconnected_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles a client disconnection event triggered by the network wrapper
        and notifies other clients.
        """
        self.client_registry.remove_client(cuuid)

        logger.info(
            f"Client Disconnected (Handled by Wrapper). CUUID: {cuuid}"
        )

        self.notify_client(cuuid, event_data)

    def handle_push_self_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Registers a new client or updates an existing one with initial map
        and character data, then notifies others.
        """
        if cuuid in self.client_registry.registry:
            # Reconnection logic
            self.client_registry.set_client_data(cuuid, "is_away", False)
            self.client_registry.set_client_data(
                cuuid, "ping_timestamp", datetime.now()
            )
            logger.info(f"Player {cuuid} has returned to the world.")
        else:
            # New player logic
            self.client_registry.register_client(
                cuuid, event_data.map_name, event_data.char_dict
            )

        self.notify_populate_client(cuuid, event_data)

    def handle_ping_event(self, cuuid: str, event_data: EventData) -> None:
        """
        Updates the ping timestamp for a client to indicate they are still
        connected.
        """
        self.client_registry.set_client_data(
            cuuid, "ping_timestamp", datetime.now()
        )

    def handle_client_interaction_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Processes a client interaction event, updates character data, and
        notifies the target client.
        """
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client_interaction(cuuid, event_data)

    def handle_client_response_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles a response from a client, updates their character data, and
        notifies other clients.
        """
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client(cuuid, event_data)

    def handle_key_event(
        self, cuuid: str, event_data: EventData, pressed: bool
    ) -> None:
        """
        Handles key press or release events (e.g., SHIFT) and updates the
        client's running state accordingly.
        """
        if event_data.kb_key == "SHIFT":
            self.client_registry.set_client_data(
                cuuid, "char_dict", {"running": pressed}
            )
        self.notify_client(cuuid, event_data)

    def handle_start_battle_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles the start of a battle by updating the client's character state
        and notifying others.
        """
        self.client_registry.update_char_field(cuuid, "running", False)
        self.update_char_dict(cuuid, event_data.char_dict)
        self.client_registry.set_client_data(
            cuuid, "map_name", event_data.map_name
        )
        self.notify_client(cuuid, event_data)

    def update_char_dict(self, cuuid: str, char_data: CharData | None) -> None:
        """
        Updates the character dictionary for a client with new data.
        """
        self.client_registry.update_char_dict(cuuid, char_data)

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        """
        Sends an event notification to all clients except the originator.
        """
        self.notification_manager.notify_client(cuuid, event_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Notifies all clients about a newly joined client and sends existing
        client data to the new client.
        """
        self.notification_manager.notify_populate_client(cuuid, event_data)

    def notify_client_interaction(
        self, cuuid: str, event_data: EventData | None
    ) -> None:
        """
        Notifies a target client that another client has interacted with them.
        Skips if event data is missing.
        """
        if event_data is None:
            logger.warning(
                f"No event data provided for interaction from CUUID: {cuuid}"
            )
            return

        self.notification_manager.notify_client_interaction(cuuid, event_data)

    def send_notification(self, target_id: str, event_data: EventData) -> None:
        """
        Sends a direct event notification to a specific client.
        """
        self.notification_manager.send_notification(target_id, event_data)


class EventRouter:
    """
    Routes incoming EventData to the appropriate handler based on EventType.
    Ensures deduplication and freshness of events.
    """

    def __init__(
        self,
        registry: dict[str, dict[str, Any]],
        get_next_event_number: Callable[[], int],
    ) -> None:
        self.registry = registry
        self.get_next_event_number = get_next_event_number
        self.handlers: dict[str, Callable[[str, EventData], None]] = {}

    def register_handler(
        self, event_type: EventType, handler: Callable[[str, EventData], None]
    ) -> None:
        self.handlers[event_type.value] = handler

    def route_event(self, cuuid: str, event_data: EventData) -> None:
        if cuuid not in self.registry:
            logger.warning(f"CUUID {cuuid} not found in registry.")
            return

        event_key = event_data.type.value  # use string key consistently
        event_list = self.registry[cuuid].setdefault("event_list", {})
        last_event_number = event_list.get(event_key, -1)

        if event_data.event_number <= last_event_number:
            return

        event_list[event_key] = event_data.event_number

        handler = self.handlers.get(event_key)
        if handler:
            handler(cuuid, event_data)
        else:
            logger.warning(f"Unhandled event type: {event_key}")


class ClientRegistry:
    """
    Manages client connection state, character data, and timeout handling.
    """

    def __init__(self, timeout: int, grace_period: int = 60) -> None:
        self.registry: dict[str, dict[str, Any]] = {}
        self.timeout = timeout  # Heartbeat timeout
        self.grace_period = grace_period

    def set_client_data(self, cuuid: str, key: str, value: Any) -> None:
        if cuuid in self.registry:
            self.registry[cuuid][key] = value

    def register_client(
        self,
        cuuid: str,
        map_name: str | None = None,
        char_dict: CharData | None = None,
    ) -> None:
        default_char = CharData(
            tile_pos=(0, 0), name="", facing=Direction.DOWN, running=False
        )

        self.registry[cuuid] = {
            "map_name": map_name or "",
            "char_dict": char_dict or default_char,
            "ping_timestamp": datetime.now(),
            "event_list": {},
        }

    def update_char_field(self, cuuid: str, key: str, value: Any) -> None:
        if cuuid not in self.registry:
            return

        existing = self.registry[cuuid].get("char_dict")

        if isinstance(existing, CharData):
            self.registry[cuuid]["char_dict"] = replace(
                existing, **{key: value}
            )
        elif isinstance(existing, dict):
            existing[key] = value

    def update_char_dict(self, cuuid: str, char_data: CharData | None) -> None:
        if cuuid not in self.registry:
            return

        if char_data is None:
            logger.warning(f"No character data provided for CUUID: {cuuid}")
            return

        existing = self.registry[cuuid].get("char_dict")
        char_data_dict = asdict(char_data)

        if isinstance(existing, dict):
            existing.update(char_data_dict)
        elif isinstance(existing, CharData):
            self.registry[cuuid]["char_dict"] = replace(
                existing, **char_data_dict
            )
        else:
            self.registry[cuuid]["char_dict"] = char_data

    def remove_client(self, cuuid: str) -> None:
        if cuuid in self.registry:
            del self.registry[cuuid]

    def check_timeouts(self, now: datetime) -> list[str]:
        to_permanently_remove = []
        for cuuid, data in self.registry.items():
            last_ping = data.get("ping_timestamp", now)
            # If they are currently disconnected (no active socket)
            if data.get("is_away", False):
                if (now - last_ping).seconds > self.grace_period:
                    to_permanently_remove.append(cuuid)
            # Normal heartbeat check for active clients
            elif (now - last_ping).seconds > self.timeout:
                data["is_away"] = True

        return to_permanently_remove


class NotificationManager:
    """
    Handles sending event notifications to clients via the WebSocket server.
    """

    def __init__(
        self,
        server: WebsocketServerWrapper,
        get_next_event_number: Callable[[], int],
        event_factory: EventFactory,
        client_registry: ClientRegistry,
    ) -> None:
        self.server = server
        self.get_next_event_number = get_next_event_number
        self.event_factory = event_factory
        self.client_registry = client_registry

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        """Serializes once and broadcasts to all other clients."""
        updated_event = event_data.copy(cuuid=cuuid)
        json_data = json.dumps(updated_event.to_dict())
        self.server.notify_broadcast(exclude_cuuid=cuuid, json_data=json_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        new_client_event = json.dumps(event_data.copy(cuuid=cuuid).to_dict())
        self.server.notify_broadcast(
            exclude_cuuid=cuuid, json_data=new_client_event
        )

        for client_id, data in self.client_registry.registry.items():
            if client_id == cuuid:
                continue

            existing_client_event = self.event_factory.create_event(
                event_type=event_data.type,
                cuuid=client_id,
                map_name=data["map_name"],
                char_dict=data["char_dict"],
            )
            self.send_notification(cuuid, existing_client_event)

    def notify_client_interaction(
        self, cuuid: str, event_data: EventData
    ) -> None:
        if event_data is None or event_data.target is None:
            logger.warning(f"Invalid interaction event from CUUID: {cuuid}")
            return

        updated_event = event_data.copy(cuuid=cuuid)
        json_data = json.dumps(updated_event.to_dict())
        self.server.notify(event_data.target, json_data)

    def send_notification(self, target_id: str, event_data: EventData) -> None:
        json_data = json.dumps(event_data.to_dict())
        self.server.notify(target_id, json_data)


class EventFactory:
    """
    Utility class for creating standardized EventData objects.
    """

    def __init__(self, get_next_event_number: Callable[[], int]) -> None:
        self.get_next_event_number = get_next_event_number

    def create_event(
        self,
        event_type: EventType,
        cuuid: str,
        map_name: str = "",
        char_dict: dict[str, Any] | CharData | None = None,
        target: str | None = None,
    ) -> EventData:

        if isinstance(char_dict, dict):
            base = asdict(
                CharData(
                    tile_pos=(0, 0),
                    name="",
                    facing=Direction.DOWN,
                    running=False,
                )
            )
            merged = {**base, **char_dict}
            char_dict = CharData(**merged)

        return EventData(
            type=event_type,
            event_number=self.get_next_event_number(),
            cuuid=cuuid,
            map_name=map_name,
            char_dict=char_dict,
            target=target,
        )
