# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from typing import Any

from tuxemon.db import GameCondition

logger = logging.getLogger(__name__)


class ScopeVariablesManager:
    """
    Base class for managing a single scope of game variables.
    Tracks whether the internal state has changed since last check.
    """

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._variables: dict[str, Any] = initial.copy() if initial else {}
        self._dirty: bool = False

    def get(self, key: str, default: Any | None = None) -> Any:
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

    def update(self, data: dict[str, Any]) -> None:
        """
        Update multiple variables at once. Marks the manager as dirty
        if any value changes or new keys are added.
        """
        for key, value in data.items():
            if self._variables.get(key) != value:
                self._variables[key] = value
                self._dirty = True

    def is_dirty(self) -> bool:
        return self._dirty

    def clear_dirty(self) -> None:
        self._dirty = False

    def find_highest(self, keys: list[str]) -> tuple[float, list[str]]:
        highest_value = float("-inf")
        highest_keys = []

        for key in keys:
            if key in self._variables:
                try:
                    value = float(self._variables[key])
                except ValueError:
                    raise ValueError(f"The value of '{key}' is not a number")
                if value > highest_value:
                    highest_value = value
                    highest_keys = [key]
                elif value == highest_value:
                    highest_keys.append(key)

        return highest_value, highest_keys

    def find_lowest(self, keys: list[str]) -> tuple[float, list[str]]:
        lowest_value = float("inf")
        lowest_keys = []

        for key in keys:
            if key in self._variables:
                try:
                    value = float(self._variables[key])
                except ValueError:
                    raise ValueError(f"The value of '{key}' is not a number")
                if value < lowest_value:
                    lowest_value = value
                    lowest_keys = [key]
                elif value == lowest_value:
                    lowest_keys.append(key)

        return lowest_value, lowest_keys


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
        initial_player: dict[str, Any] | None = None,
        initial_world: dict[str, Any] | None = None,
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

    def is_any_dirty(self) -> bool:
        return self.player.is_dirty() or self.world.is_dirty()

    def clear_all_dirty(self) -> None:
        self.player.clear_dirty()
        self.world.clear_dirty()

    def _resolve_value(self, key: str) -> Any:
        if self.player.has(key):
            return self.player.get(key)
        return self.world.get(key)

    def _evaluate_conditions(
        self,
        entries: Sequence[tuple[str, Any, str | None, str | None]],
    ) -> bool:
        for key, expected, description, scope in entries:
            # Scope-aware resolution
            if scope == "player":
                current = self.player.get(key)
            elif scope == "world":
                current = self.world.get(key)
            else:
                current = self._resolve_value(key)

            if current != expected:
                reason = description or f"Variable '{key}' check"
                logger.debug(
                    f"Condition Failed: {reason} "
                    f"(Expected {expected}, Got {current})"
                )
                return False

        return True

    def _collect_missing(
        self,
        entries: Sequence[tuple[str, Any, str | None, str | None]],
    ) -> list[str]:
        missing: list[str] = []

        for key, expected, description, scope in entries:
            # Scope-aware resolution
            if scope == "player":
                current = self.player.get(key)
            elif scope == "world":
                current = self.world.get(key)
            else:
                current = self._resolve_value(key)

            if current != expected:
                msg = description or f"Missing requirement: {key}"
                missing.append(msg)

        return missing

    def check_logic(self, conditions: Sequence[dict[str, Any]]) -> bool:
        """
        Evaluate simple dict-based variable checks using the unified condition engine.
        Each dict maps keys to expected values. All entries must match for success.
        """
        entries = []
        for cond in conditions:
            for key, value in cond.items():
                entries.append((key, value, None, None))
        return self._evaluate_conditions(entries)

    def check_conditions(self, conditions: Sequence[GameCondition]) -> bool:
        """
        Evaluate typed GameCondition entries using the unified condition engine.
        Supports per-condition scope and optional human-readable descriptions.
        """
        entries = [
            (cond.key, cond.value, cond.description, cond.scope)
            for cond in conditions
        ]
        return self._evaluate_conditions(entries)

    def get_missing_requirements(
        self, conditions: Sequence[GameCondition]
    ) -> list[str]:
        """
        Return descriptions for all GameCondition entries that fail their checks.
        Uses the unified condition engine to collect every mismatch.
        """
        if not conditions:
            return []

        entries = [
            (cond.key, cond.value, cond.description, cond.scope)
            for cond in conditions
        ]

        return self._collect_missing(entries)
