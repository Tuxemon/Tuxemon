# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.player import Player
    from tuxemon.states.world.worldstate import WorldState

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


local_session = Session()
