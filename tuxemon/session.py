# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID, uuid4

from tuxemon.celestial_handler import CelestialHandler
from tuxemon.save_system import save
from tuxemon.save_system.save_state import (
    TIME_FORMAT,
    NPCState,
    SessionSave,
    WorldSave,
)
from tuxemon.time_handler import TimeHandler

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.db import BoundingBox
    from tuxemon.entity.npc import NPC
    from tuxemon.save_system.save_state import SaveData
    from tuxemon.states.world_state import WorldState

logger = logging.getLogger(__name__)


ClientType = TypeVar("ClientType", bound="BaseClient")


class AbstractSession(ABC, Generic[ClientType]):
    """
    Defines the abstract interface for all game sessions (local, network, etc.).
    This class cannot be instantiated directly.
    """

    def __init__(self) -> None:
        self._uuid: UUID = uuid4()
        self.time = TimeHandler()
        self.celestial = CelestialHandler.from_session(self)
        self._start_time: datetime = datetime.now()
        self._start_timestamp: float = time.time()
        self._total_playtime: float = 0.0
        self.current_condition_box: BoundingBox | None = None
        self._current_slot: int | None = None

        self._client: ClientType | None = None
        self._world: WorldState | None = None
        self._player: NPC | None = None
        self._session_state: SessionSave = SessionSave()

    @property
    @abstractmethod
    def client(self) -> ClientType:
        """Returns the client instance."""

    @property
    @abstractmethod
    def world(self) -> WorldState:
        """Returns the world instance."""

    @property
    @abstractmethod
    def player(self) -> NPC:
        """Returns the player instance."""

    def set_client(self, client: ClientType) -> None:
        """Sets the client. Can be overridden, but is provided for local convenience."""
        self._client = client
        logger.debug("Client initialized successfully.")

    def set_world(self, world: WorldState) -> None:
        """Sets the world. Can be overridden, but is provided for local convenience."""
        self._world = world
        logger.debug("World initialized successfully.")

    def set_player(self, player: NPC) -> None:
        """Sets the player. Can be overridden, but is provided for local convenience."""
        self._player = player
        player.is_player = True
        logger.debug("Player initialized successfully.")

    def has_player(self) -> bool:
        """Checks if a player is attached to the session."""
        return self._player is not None

    def reset(
        self,
        reset_client: bool = True,
        reset_world: bool = True,
        reset_player: bool = True,
    ) -> None:
        """Resets the main session components."""
        if reset_client:
            self._client = None
        if reset_world:
            self._world = None
        if reset_player:
            self._player = None

    def reset_time(self) -> None:
        """Resets session time tracking to start fresh."""
        self._start_time = datetime.now()
        self._start_timestamp = time.time()
        self._total_playtime = 0.0

    def get_state(self) -> SessionSave:
        """Returns session-level state to be saved and updates internal playtime."""
        current_duration = time.time() - self._start_timestamp
        self._total_playtime += current_duration
        self._start_timestamp = time.time()

        return SessionSave(
            uuid=self._uuid.hex,
            start_time=self._start_time.strftime(TIME_FORMAT),
            duration=current_duration,
            total_playtime=self._total_playtime,
        )

    def set_state(self, save_data: SessionSave) -> None:
        """Restores session-level state from saved data."""
        self._session_state = save_data
        self._total_playtime = save_data.total_playtime or 0.0


class Session(AbstractSession["BaseClient"]):
    """
    Contains Client, World, and Player.
    This is the concrete local session implementation.
    """

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            raise ValueError("Client is not initialized")
        return self._client

    @property
    def world(self) -> WorldState:
        if self._world is None:
            raise ValueError("World is not initialized")
        return self._world

    @property
    def player(self) -> NPC:
        if self._player is None:
            raise ValueError("Player is not initialized")
        return self._player

    @property
    def current_slot(self) -> int | None:
        """The slot index most recently saved or loaded."""
        return self._current_slot

    @current_slot.setter
    def current_slot(self, value: int | None) -> None:
        self._current_slot = value

    def load_state(self, save_data: SaveData) -> None:
        """
        Loads the player, world, and other session-level states from a saved game model.
        """
        self.player.set_state(self, save_data.npc_state or NPCState())
        self.world.set_state(self, save_data.world_state or WorldSave())
        self.set_state(save_data.session_state or SessionSave())
        self.client.shop_manager.load_from_dict(save_data.shop_stock)
        self.client.npc_manager.load_persistent_npc_states(
            self, save_data.persistent_state or []
        )

    def save_state(self, index: int, slot: int) -> SaveData:
        """
        Saves the player, world, and other session-level states to a dictionary.
        """
        save_data = save.get_save_data(self)
        save_path = save.get_save_path(index)
        save.save(save_data, save_path)
        self._current_slot = slot
        return save_data


local_session = Session()
