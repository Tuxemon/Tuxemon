# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Tuxemon server middleware."""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Multiplayer:
    """This middleware will allow you to use the AsteriaServer for Multiplayer games and the mobile controller.
    When it receives KEYDOWN/KEYUP/NETKBD events, it will set the corresponding dictionary key in
    "network_events" to true or false. In your main game loop, you can then iterate through this dictionary
    and change the game accordingly.

    Public functions:
    event_legal -- Returns True for all events that pass the legal logic. Returns False for all events that
                   fail legal logic.
    event_execute -- Sets the game_server.network_events dictionary based on what key was pressed

    """

    def __init__(self, game_server: Any = None) -> None:
        self.game_server = game_server
        self.server = None

    def event_legal(self, cuuid: str, euuid: str, event_data: Any) -> bool:
        if event_data["type"] == "PUSH_SELF":
            return True
        if event_data["type"] == "CLIENT_MOVE_START":
            return True
        if event_data["type"] == "CLIENT_MAP_UPDATE":
            return True
        if event_data["type"] == "CLIENT_MOVE_COMPLETE":
            return True
        if event_data["type"] == "CLIENT_KEYDOWN":
            return True
        if event_data["type"] == "CLIENT_KEYUP":
            return True
        if event_data["type"] == "CLIENT_FACING":
            return True
        if event_data["type"] == "CLIENT_INTERACTION":
            return True
        if event_data["type"] == "CLIENT_RESPONSE":
            return True
        if event_data["type"] == "CLIENT_START_BATTLE":
            return True
        if event_data["type"] == "PING":
            return True
        else:
            return False

    def event_execute(self, cuuid: str, euuid: str, event_data: Any) -> None:
        self.game_server.server_event_handler(cuuid, event_data)


class Controller:
    """This middleware will allow you to use the AsteriaServer for Multiplayer games and the mobile controller.
    When it receives KEYDOWN/KEYUP events, it will set the corresponding dictionary key in
    "network_events" to true or false. In your main game loop, you can then iterate through this dictionary
    and change the game accordingly.

    Public functions:
    event_legal -- Returns True for all events that pass the legal logic. Returns False for all events that
                   fail legal logic.
    event_execute -- Sets the game_server.network_events dictionary based on what key was pressed

    """

    def __init__(self, game_server: Any = None) -> None:
        self.game_server = game_server
        self.server = None

    def event_legal(
        self, cuuid: str, euuid: str, event_data: Any
    ) -> Optional[bool]:
        if "KEYDOWN:" in event_data or "KEYUP:" in event_data:
            return True
        return None

    def event_execute(self, cuuid: str, euuid: str, event_data: Any) -> None:
        if "KEYDOWN:" in event_data or "KEYUP:" in event_data:
            self.game_server.network_events.append(event_data)
