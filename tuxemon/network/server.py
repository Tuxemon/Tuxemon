# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import datetime
from itertools import count
from pathlib import Path
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
        self.state_dir = Path.cwd() / "server"
        self.state_file = self.state_dir / "characters.json"
        self.character_state_store: dict[str, dict[str, Any]] = {}
        self.server.max_clients = 32
        self.listening = False
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
        self._load_character_states()


    def _load_character_states(self) -> None:
        """Load persisted character states from server folder."""
        try:
            if not self.state_file.exists():
                return
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                self.character_state_store = payload
                logger.info(
                    "Loaded %s persisted character states from %s",
                    len(self.character_state_store),
                    self.state_file,
                )
        except Exception as e:
            logger.warning("Failed to load persisted character states: %s", e)

    def _save_character_states(self) -> None:
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(self.character_state_store, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to persist character states: %s", e)

    def _emit_server_log(self, message: str) -> None:
        """Emit a server log to module logger and websocket terminal stream."""
        emit = getattr(self.server, "_emit_terminal_log", None)
        if callable(emit):
            emit(f"[SERVER] {message}")
            return
        logger.warning(message)

    def _party_size(self, data: dict[str, Any] | None) -> int:
        if not isinstance(data, dict):
            return 0
        monsters = data.get("monsters")
        return len(monsters) if isinstance(monsters, list) else 0

    def _char_data_to_dict(
        self, char_data: CharData | dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if not char_data:
            return None
        return char_data.to_dict() if isinstance(char_data, CharData) else dict(char_data)

    def _normalize_wallet(self, wallet_address: str | None) -> str:
        if not isinstance(wallet_address, str):
            return ""
        return wallet_address.strip()

    def _state_key(self, wallet_address: str | None, cuuid: str) -> str:
        wallet = self._normalize_wallet(wallet_address)
        return wallet or cuuid

    def _normalize_character_name(self, name: str | None, wallet_address: str) -> str:
        parsed = str(name or "").strip()
        if parsed.lower() in {"", "red", "unnamed player"} and wallet_address:
            return wallet_address
        return parsed or "Unnamed Player"

    def _sanitize_saved_char_dict(
        self, char_dict: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Normalizes persisted payloads from older builds before decoding."""
        if not isinstance(char_dict, dict):
            return None

        cleaned = dict(char_dict)
        facing = cleaned.get("facing")
        if isinstance(facing, str):
            cleaned["facing"] = facing.upper()

        tile_pos = cleaned.get("tile_pos")
        if isinstance(tile_pos, tuple):
            cleaned["tile_pos"] = list(tile_pos)

        return cleaned

    def _persist_character_state(
        self,
        cuuid: str,
        wallet_or_map: str | None,
        map_name_or_char: str | CharData | dict[str, Any] | None = None,
        char_data: CharData | dict[str, Any] | None = None,
    ) -> None:
        """Persist character state.

        Supports both current calls:
            _persist_character_state(cuuid, wallet, map_name, char_data)
        and legacy calls still seen in some builds:
            _persist_character_state(cuuid, map_name, char_data)
        """
        wallet_address: str | None
        map_name: str | None

        if char_data is None and not isinstance(map_name_or_char, str):
            wallet_address = ""
            map_name = wallet_or_map
            char_payload = map_name_or_char
        else:
            wallet_address = wallet_or_map
            map_name = map_name_or_char if isinstance(map_name_or_char, str) else None
            char_payload = char_data

        data = self._char_data_to_dict(char_payload)
        if not data:
            return

        wallet = self._normalize_wallet(wallet_address)
        data["name"] = self._normalize_character_name(data.get("name"), wallet)

        key = self._state_key(wallet, cuuid)
        previous = self.character_state_store.get(key)

        prev_char_dict = None
        prev_map = None
        if isinstance(previous, dict):
            prev_char_dict = (
                previous.get("char_dict") if isinstance(previous.get("char_dict"), dict) else None
            )
            prev_map = previous.get("map_name")

        current_map = map_name or ""
        if prev_map == current_map and prev_char_dict == data:
            return

        entry = {
            "cuuid": cuuid,
            "wallet_address": wallet,
            "map_name": current_map,
            "char_dict": data,
            "updated_at": datetime.now().isoformat(),
        }
        self.character_state_store[key] = entry
        self._emit_server_log(f"Saved character state: key={key} cuuid={cuuid} map={entry['map_name']}")

        prev_name = None
        prev_tile_pos = None
        if isinstance(previous, dict):
            prev_name = prev_char_dict.get("name") if prev_char_dict else None
            prev_tile_pos = prev_char_dict.get("tile_pos") if prev_char_dict else None

        current_name = data.get("name")
        current_map = entry["map_name"]
        current_tile_pos = data.get("tile_pos")
        prev_party_size = self._party_size(prev_char_dict)
        current_party_size = self._party_size(data)

        if (
            prev_name != current_name
            or prev_map != current_map
            or prev_tile_pos != current_tile_pos
            or prev_party_size != current_party_size
        ):
            self._emit_server_log(
                f"Character state changed: wallet={wallet or '(none)'} name={current_name} map={current_map} tile_pos={current_tile_pos} party_size={current_party_size}"
            )

        if prev_name != current_name:
            self._emit_server_log(
                f"Persisted character rename to characters.json: wallet={wallet or '(none)'} old_name={prev_name or '(unset)'} new_name={current_name}"
            )

        if prev_map != current_map:
            self._emit_server_log(
                f"Persisted character map change to characters.json: wallet={wallet or '(none)'} old_map={prev_map or '(unset)'} new_map={current_map}"
            )

        if prev_tile_pos != current_tile_pos:
            self._emit_server_log(
                f"Persisted character position change to characters.json: wallet={wallet or '(none)'} old_tile_pos={prev_tile_pos} new_tile_pos={current_tile_pos}"
            )

        if prev_party_size != current_party_size:
            self._emit_server_log(
                f"Persisted party size change to characters.json: wallet={wallet or '(none)'} old_party_size={prev_party_size} new_party_size={current_party_size}"
            )

        self._save_character_states()

    def _get_saved_state(self, wallet_address: str | None, cuuid: str) -> dict[str, Any] | None:
        return self.character_state_store.get(self._state_key(wallet_address, cuuid))

    def _persist_registry_state(self, cuuid: str) -> None:
        data = self.client_registry.registry.get(cuuid)
        if not data:
            return
        self._persist_character_state(
            cuuid,
            data.get("wallet_address"),
            data.get("map_name"),
            data.get("char_dict"),
        )

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
            EventType.CLIENT_MAP_UPDATE, self.handle_map_update_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_FACING, self.handle_facing_event
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

    def start_hosting(self) -> bool:
        """Starts websocket listening for multiplayer hosting."""
        if self.listening:
            return True
        started = self.server.start_listening(self.server_port)
        self.listening = bool(started)
        if self.listening:
            logger.info("TuxemonServer: Hosting started on %s", self.server_port)
            return True

        logger.error(
            "TuxemonServer: Failed to host on port %s (already in use or startup failure)",
            self.server_port,
        )
        return False

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
                normalized = self._normalize_event_dict(cuuid, event_dict)
                if normalized is None:
                    continue
                event_data = EventData.from_dict(normalized)
                self.server_event_handler(cuuid, event_data)
                if event_data.type != EventType.PING:
                    self._persist_registry_state(cuuid)
                logger.warning("Processed event: cuuid=%s type=%s", cuuid, event_data.type.value)
            except Exception:
                logger.exception(f"Critical error handling event from {cuuid}")

        timed_out = self.client_registry.check_timeouts(self.server_timestamp)
        for cuuid in timed_out:
            self._handle_timeout_disconnection(cuuid)

    def _normalize_event_dict(
        self, cuuid: str, event_dict: Any
    ) -> dict[str, Any] | None:
        """Normalizes incoming network payloads before EventData decoding."""
        if not isinstance(event_dict, dict):
            logger.warning(
                "Ignoring malformed event from %s: expected dict, got %s",
                cuuid,
                type(event_dict).__name__,
            )
            return None

        normalized = dict(event_dict)

        if "type" not in normalized:
            logger.warning(
                "Ignoring malformed event from %s: missing event type",
                cuuid,
            )
            return None

        normalized.setdefault("event_number", self.get_next_event_number())
        return normalized

    def _handle_timeout_disconnection(self, cuuid: str) -> None:
        """Internal helper to clean up a timed-out client."""
        logger.warning(
            "Client timeout: cuuid=%s wallet=%s",
            cuuid,
            self.client_registry.registry.get(cuuid, {}).get("wallet_address", ""),
        )
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
        wallet = self._normalize_wallet(event_data.wallet_address)

        saved_state = self._get_saved_state(wallet, cuuid)

        if saved_state:
            saved_char = self._sanitize_saved_char_dict(saved_state.get("char_dict"))
            if isinstance(saved_char, dict) and {"tile_pos", "facing", "name"}.issubset(saved_char):
                if isinstance(event_data, EventData):
                    event_data = event_data.copy(
                        map_name=saved_state.get("map_name") or event_data.map_name,
                        char_dict=CharData.from_dict(saved_char),
                    )
                else:
                    event_data.map_name = saved_state.get("map_name") or event_data.map_name
                    event_data.char_dict = saved_char

        if cuuid in self.client_registry.registry:
            # Reconnection logic
            self.client_registry.set_client_data(cuuid, "is_away", False)
            self.client_registry.set_client_data(
                cuuid, "ping_timestamp", datetime.now()
            )
            self.client_registry.set_client_data(cuuid, "wallet_address", wallet)
            logger.warning(f"Player {cuuid} has returned to the world.")
        else:
            # New player logic
            self.client_registry.register_client(
                cuuid, event_data.map_name, event_data.char_dict, wallet
            )

        if event_data.char_dict and event_data.map_name:
            map_name = event_data.map_name
            payload = self._char_data_to_dict(event_data.char_dict) or {}
            payload["name"] = self._normalize_character_name(payload.get("name"), wallet)
            self.client_registry.set_client_data(cuuid, "char_dict", payload)

            if isinstance(event_data, EventData):
                event_data = event_data.copy(
                    char_dict=CharData.from_dict(payload),
                    wallet_address=wallet,
                )

            logger.warning(
                "Client connected: cuuid=%s wallet=%s name=%s map=%s active_clients=%s",
                cuuid,
                wallet or "(none)",
                payload["name"],
                map_name,
                len(self.client_registry.registry),
            )
            self._persist_character_state(
                cuuid, wallet, map_name, payload
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

    def handle_map_update_event(self, cuuid: str, event_data: EventData) -> None:
        previous_name = None
        existing = self.client_registry.registry.get(cuuid, {}).get("char_dict")
        if isinstance(existing, CharData):
            previous_name = existing.name
        elif isinstance(existing, dict):
            previous_name = existing.get("name")

        incoming_name = None
        if isinstance(event_data.char_dict, CharData):
            incoming_name = event_data.char_dict.name
        elif isinstance(event_data.char_dict, dict):
            incoming_name = event_data.char_dict.get("name")

        wallet = self.client_registry.registry.get(cuuid, {}).get("wallet_address", "")
        logger.warning(
            "Map update: cuuid=%s map=%s wallet=%s",
            cuuid,
            event_data.map_name,
            wallet,
        )
        if (
            isinstance(incoming_name, str)
            and incoming_name.strip()
            and previous_name != incoming_name
        ):
            logger.warning(
                "Character rename detected: cuuid=%s wallet=%s old_name=%s new_name=%s",
                cuuid,
                self.client_registry.registry.get(cuuid, {}).get(
                    "wallet_address", ""
                )
                or "(none)",
                previous_name or "(unset)",
                incoming_name,
            )
        previous_party_size = 0
        if isinstance(existing, CharData):
            previous_party_size = len(existing.monsters or [])
        elif isinstance(existing, dict) and isinstance(existing.get("monsters"), list):
            previous_party_size = len(existing.get("monsters") or [])

        incoming_party_size = 0
        if isinstance(event_data.char_dict, CharData):
            incoming_party_size = len(event_data.char_dict.monsters or [])
        elif isinstance(event_data.char_dict, dict) and isinstance(event_data.char_dict.get("monsters"), list):
            incoming_party_size = len(event_data.char_dict.get("monsters") or [])

        if incoming_party_size != previous_party_size:
            self._emit_server_log(
                f"Incoming party size change detected: cuuid={cuuid} wallet={wallet or '(none)'} old_party_size={previous_party_size} new_party_size={incoming_party_size}"
            )
        self.client_registry.set_client_data(cuuid, "map_name", event_data.map_name)
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client(cuuid, event_data)

    def handle_facing_event(self, cuuid: str, event_data: EventData) -> None:
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client(cuuid, event_data)

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

    def update_char_dict(
        self, cuuid: str, char_data: CharData | dict[str, Any] | None
    ) -> None:
        """Updates character state and persists it to server folder."""
        self.client_registry.update_char_dict(cuuid, char_data)
        map_name = None
        wallet = None
        merged_char_data: CharData | dict[str, Any] | None = None
        if cuuid in self.client_registry.registry:
            map_name = self.client_registry.registry[cuuid].get("map_name")
            wallet = self.client_registry.registry[cuuid].get("wallet_address")
            merged_char_data = self.client_registry.registry[cuuid].get("char_dict")

        self._persist_character_state(cuuid, wallet, map_name, merged_char_data)

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
        event_key = event_data.type.value  # use string key consistently

        handler = self.handlers.get(event_key)
        if not handler:
            logger.warning(f"Unhandled event type: {event_key}")
            return

        if cuuid not in self.registry:
            if event_key == EventType.PUSH_SELF.value:
                handler(cuuid, event_data)
                return
            logger.warning(f"CUUID {cuuid} not found in registry.")
            return

        event_list = self.registry[cuuid].setdefault("event_list", {})
        last_event_number = event_list.get(event_key, -1)

        if event_data.event_number <= last_event_number:
            return

        event_list[event_key] = event_data.event_number
        handler(cuuid, event_data)


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
        wallet_address: str = "",
    ) -> None:
        default_char = CharData(
            tile_pos=(0, 0), name="", facing=Direction.DOWN, running=False
        )

        self.registry[cuuid] = {
            "map_name": map_name or "",
            "char_dict": char_dict or default_char,
            "ping_timestamp": datetime.now(),
            "event_list": {},
            "wallet_address": wallet_address,
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

    def update_char_dict(
        self, cuuid: str, char_data: CharData | dict[str, Any] | None
    ) -> None:
        if cuuid not in self.registry:
            return

        if char_data is None:
            logger.warning(f"No character data provided for CUUID: {cuuid}")
            return

        existing = self.registry[cuuid].get("char_dict")
        if isinstance(char_data, CharData):
            char_data_dict = asdict(char_data)
        elif isinstance(char_data, dict):
            char_data_dict = dict(char_data)
        else:
            logger.warning("Invalid character data type for CUUID %s", cuuid)
            return

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
        logger.warning("Broadcasting event type=%s from cuuid=%s", updated_event.type.value, cuuid)
        self.server.notify_broadcast(exclude_cuuid=cuuid, json_data=json_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        logger.warning(
            "Broadcasting PUSH_SELF for %s to %s peers",
            cuuid,
            max(0, len(self.client_registry.registry) - 1),
        )
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
            logger.warning(
                "Sending existing client snapshot %s -> newcomer %s",
                client_id,
                cuuid,
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
