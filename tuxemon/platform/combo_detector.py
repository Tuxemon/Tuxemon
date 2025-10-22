# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import ButtonEdgeFilter

logger = logging.getLogger(__name__)


@dataclass
class _TrieNode:
    """A node in the combo detection Trie."""

    children: dict[int, _TrieNode] = field(default_factory=dict)
    callback: Optional[Callable[[], None]] = None
    max_delay_s: Optional[float] = None


@dataclass
class _ActiveCombo:
    """Represents a potential combo match in progress."""

    node: _TrieNode
    last_timestamp: float


class ComboManager:
    def __init__(self) -> None:
        self.detector = ComboDetector()
        self.edge_filter = ButtonEdgeFilter()

    def process(self, event: PlayerInput) -> None:
        if self.edge_filter.is_new_press(event.button, event.pressed):
            self.detector.process_input(event)


class ComboDetector:
    """
    Detects button combinations based on a stream of inputs using a Trie.
    """

    def __init__(self) -> None:
        self._trie = _TrieNode()
        self._active_combos: list[_ActiveCombo] = []

    def add_combo(
        self,
        buttons: list[int],
        callback: Callable[[], None],
        max_delay_ms: float,
    ) -> None:
        """
        Adds a combo pattern to the Trie.
        """
        node = self._trie
        max_delay_s = max_delay_ms / 1000.0
        for button in buttons:
            if button not in node.children:
                node.children[button] = _TrieNode()
            node = node.children[button]
            node.max_delay_s = max_delay_s
        node.callback = callback

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

        # Prune orphaned nodes
        for button, parent in reversed(path):
            child = parent.children[button]
            if child.callback is None and not child.children:
                del parent.children[button]
            else:
                break

        return True

    def process_input(self, input_event: PlayerInput) -> None:
        """
        Processes a single input event and checks for any matching combos
        by traversing the Trie.
        """
        # Add a new potential combo path starting from the root.
        new_active_combos: list[_ActiveCombo] = []
        if input_event.button in self._trie.children:
            new_active_combos.append(
                _ActiveCombo(
                    self._trie.children[input_event.button],
                    input_event.timestamp,
                )
            )

        # Extend existing active combo paths.
        for active_combo in self._active_combos:
            time_diff = input_event.timestamp - active_combo.last_timestamp
            if input_event.button in active_combo.node.children and (
                active_combo.node.max_delay_s is None
                or time_diff <= active_combo.node.max_delay_s
            ):
                new_active_combos.append(
                    _ActiveCombo(
                        active_combo.node.children[input_event.button],
                        input_event.timestamp,
                    )
                )

        # Check if any new paths resulted in a successful combo match.
        for active_combo in new_active_combos:
            if active_combo.node.callback:
                active_combo.node.callback()
                logger.info("Combo detected, clearing paths.")
                self._active_combos.clear()
                return

        self._active_combos = new_active_combos
