# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import ButtonEdgeFilter

logger = logging.getLogger(__name__)


@dataclass
class _TrieNode:
    """A node in the combo detection Trie."""

    children: dict[int, _TrieNode] = field(default_factory=dict)
    callback: Callable[[], None] | None = None
    max_delay_s: float | None = None
    priority: int = 0
    length: int = 0
    trigger_on_release: bool = False


@dataclass
class _ActiveCombo:
    """Represents a potential combo match in progress."""

    node: _TrieNode
    last_timestamp: float
    start_timestamp: float
    last_button: int | None = None


@dataclass
class ComboProfile:
    name: str
    buttons: list[int]
    callback: Callable[[], None]
    delays_s: list[float] | None = None
    description: str = ""
    character: str | None = None
    difficulty: int = 1  # 1 = easy, 2 = medium, 3 = hard
    priority: int = 0
    trigger_on_release: bool = False


class ComboManager:
    def __init__(self) -> None:
        self.detector = ComboDetector()
        self.edge_filter = ButtonEdgeFilter()
        self.hold_start: dict[int, float] = {}

    def process(self, event: PlayerInput) -> None:
        # Detect new press
        if self.edge_filter.is_new_press(event.button, event.pressed):
            self.hold_start[event.button] = event.timestamp
            self.detector.process_input(event)

        # Detect release
        elif self.edge_filter.is_new_release(event.button, event.pressed):
            hold_time = event.timestamp - self.hold_start.get(
                event.button, event.timestamp
            )
            self.detector.process_input(event, hold_time=hold_time)


class ComboDetector:
    """
    Detects button combinations based on a stream of inputs using a Trie.
    """

    def __init__(self, global_window_s: float = 2.0):
        self._trie = _TrieNode()
        self._active_combos: list[_ActiveCombo] = []
        self._global_window_s = global_window_s

    def add_combo(self, profile: ComboProfile) -> None:
        node = self._trie
        num_buttons = len(profile.buttons)

        has_valid_delays = (
            profile.delays_s and len(profile.delays_s) == num_buttons - 1
        )

        for i, button in enumerate(profile.buttons):
            if button not in node.children:
                node.children[button] = _TrieNode()

            child = node.children[button]
            child.length = i + 1

            if profile.delays_s and has_valid_delays and i < num_buttons - 1:
                child.max_delay_s = profile.delays_s[i]

            node = child

        node.callback = profile.callback
        node.priority = profile.priority
        node.trigger_on_release = profile.trigger_on_release

    def remove_combo(self, buttons: list[int]) -> bool:
        """Removes a combo pattern from the Trie."""
        path: list[tuple[int, _TrieNode]] = []
        node = self._trie

        # Traverse the Trie and record the path
        for button in buttons:
            if button not in node.children:
                return False  # Combo not found
            path.append((button, node))
            node = node.children[button]

        # Remove the callback
        if node.callback is None:
            return False  # No combo to remove
        node.callback = None
        node.priority = 0

        # Prune orphaned nodes
        for button, parent in reversed(path):
            child = parent.children[button]
            if (
                child.callback is None
                and child.priority == 0
                and not child.children
            ):
                del parent.children[button]
            else:
                break

        return True

    def process_input(
        self, event: PlayerInput, hold_time: float = 0.0
    ) -> None:
        now = event.timestamp

        fresh = self._prune_expired(now)
        new = self._advance_trie(event, now, fresh)

        completed: list[_ActiveCombo] = []
        completed.extend(self._check_press_completion(new, now))
        completed.extend(self._check_release_completion(event, hold_time, now))

        if completed:
            self._fire_best(completed)
            self._active_combos.clear()
        else:
            self._active_combos = new

    def _prune_expired(self, now: float) -> list[_ActiveCombo]:
        return [
            ac
            for ac in self._active_combos
            if (now - ac.start_timestamp) <= self._global_window_s
        ]

    def _advance_trie(
        self, event: PlayerInput, now: float, fresh: list[_ActiveCombo]
    ) -> list[_ActiveCombo]:
        new: list[_ActiveCombo] = []

        if event.button in self._trie.children:
            new.append(
                _ActiveCombo(
                    self._trie.children[event.button],
                    now,
                    now,
                    last_button=event.button,
                )
            )

        for ac in fresh:
            diff = now - ac.last_timestamp
            if event.button in ac.node.children:
                child = ac.node.children[event.button]
                if ac.node.max_delay_s is None or diff <= ac.node.max_delay_s:
                    new.append(
                        _ActiveCombo(
                            child,
                            now,
                            ac.start_timestamp,
                            last_button=event.button,
                        )
                    )
        return new

    def _check_press_completion(
        self, combos: list[_ActiveCombo], now: float
    ) -> list[_ActiveCombo]:
        return [
            ac
            for ac in combos
            if ac.node.callback
            and not ac.node.trigger_on_release
            and (now - ac.start_timestamp) <= self._global_window_s
        ]

    def _check_release_completion(
        self, event: PlayerInput, hold_time: float, now: float
    ) -> list[_ActiveCombo]:
        try:
            val = int(event.value)
        except (ValueError, TypeError):
            return []
        if val != 0 or hold_time <= 0:
            return []
        return [
            ac
            for ac in self._active_combos
            if ac.node.callback
            and ac.node.trigger_on_release
            and (now - ac.start_timestamp) <= self._global_window_s
            and ac.last_button == event.button
        ]

    def _fire_best(self, completed: list[_ActiveCombo]) -> None:
        best = max(
            completed, key=lambda ac: (ac.node.priority, ac.node.length)
        )
        if best.node.callback:
            best.node.callback()
            logger.info(
                "Combo detected: priority=%s, length=%s, callback=%s",
                best.node.priority,
                best.node.length,
                best.node.callback,
            )
