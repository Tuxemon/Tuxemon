# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tuxemon.save_state import NPCState, WorldSave

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.player import Player
    from tuxemon.save_state import SaveData
    from tuxemon.states.world_state import WorldState

logger = logging.getLogger(__name__)


class Session:
    """
    Contains Client, World, and Player.

    Eventually this will be extended to support network sessions.
    """

    def __init__(self) -> None:
        self._client: Optional[LocalPygameClient] = None
        self._world: Optional[WorldState] = None
        self._player: Optional[Player] = None

    @property
    def client(self) -> LocalPygameClient:
        if self._client is None:
            raise ValueError("Client is not initialized")
        return self._client

    @property
    def world(self) -> WorldState:
        if self._world is None:
            raise ValueError("World is not initialized")
        return self._world

    @property
    def player(self) -> Player:
        if self._player is None:
            raise ValueError("Player is not initialized")
        return self._player

    def set_client(self, client: LocalPygameClient) -> None:
        self._client = client
        logger.info("Client initialized successfully.")

    def set_world(self, world: WorldState) -> None:
        self._world = world
        logger.info("World initialized successfully.")

    def set_player(self, player: Player) -> None:
        self._player = player
        logger.info("Player initialized successfully.")

    def has_player(self) -> bool:
        return self._player is not None

    def reset(
        self,
        reset_client: bool = True,
        reset_world: bool = True,
        reset_player: bool = True,
    ) -> None:
        if reset_client:
            self._client = None
        if reset_world:
            self._world = None
        if reset_player:
            self._player = None

    def load_state(self, save_data: SaveData) -> None:
        """
        Loads the player, world, and other session-level states from a saved game dictionary.
        """
        if self._player is None or self._world is None:
            raise ValueError(
                "Player and World must be initialized before loading state."
            )

        self._player.set_state(self, save_data.get("npc_state", NPCState()))
        self._world.set_state(self, save_data.get("world_state", WorldSave()))

    def save_state(self, index: int, slot: int) -> SaveData:
        """
        Saves the player, world, and other session-level states to a dictionary.
        """
        if self._player is None or self._world is None:
            raise ValueError(
                "Player and World must be initialized before saving state."
            )

        # Local import to avoid circular dependency
        from tuxemon import save

        save_data = save.get_save_data(self)
        save.save(save_data, index)
        save.slot_number = slot

        return save_data


local_session = Session()
