# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards, Benjamin Bean
from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ScopeVariablesManager:
    """
    Base class for managing a single scope of game variables.
    Tracks whether the internal state has changed since last check.
    """

    def __init__(self, initial: Optional[dict[str, Any]] = None) -> None:
        self._variables: dict[str, Any] = initial.copy() if initial else {}
        self._dirty: bool = False

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._variables.get(key) != value:
            self._variables[key] = value
            self._dirty = True

    def has(self, key: str) -> bool:
        return key in self._variables

    def remove(self, key: str) -> bool:
        if key in self._variables:
            del self._variables[key]
            self._dirty = True
            return True
        return False

    def clear(self) -> None:
        if self._variables:
            self._variables.clear()
            self._dirty = True

    def items(self) -> Iterator[tuple[str, Any]]:
        return iter(self._variables.items())

    def get_state(self) -> dict[str, Any]:
        return self._variables.copy()

    def set_state(self, data: dict[str, Any]) -> None:
        if self._variables != data:
            self._variables.clear()
            self._variables.update(data)
            self._dirty = True

    def is_dirty(self) -> bool:
        return self._dirty

    def clear_dirty(self) -> None:
        self._dirty = False


class PlayerVariablesManager(ScopeVariablesManager):
    """
    Manages player-specific game variables.
    """


class WorldVariablesManager(ScopeVariablesManager):
    """
    Manages world-specific game variables.
    """


class GameVariablesManager:
    """
    Central manager for player and world game variables.
    Provides separate access to each scope's state.
    """

    def __init__(
        self,
        initial_player: Optional[dict[str, Any]] = None,
        initial_world: Optional[dict[str, Any]] = None,
    ) -> None:
        self._player = PlayerVariablesManager(initial_player)
        self._world = WorldVariablesManager(initial_world)

    @property
    def player(self) -> PlayerVariablesManager:
        return self._player

    @property
    def world(self) -> WorldVariablesManager:
        return self._world

    def get_player_state(self) -> dict[str, Any]:
        return self._player.get_state()

    def set_player_state(self, state: dict[str, Any]) -> None:
        self._player.set_state(state)

    def get_world_state(self) -> dict[str, Any]:
        return self._world.get_state()

    def set_world_state(self, state: dict[str, Any]) -> None:
        self._world.set_state(state)
