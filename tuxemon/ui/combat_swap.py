# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster


class SwapTracker:
    def __init__(self) -> None:
        self._swapped_this_turn: set[Monster] = set()
        self._temp_blocked_swaps: dict[Monster, str] = {}
        self._persistent_blocked_swaps: dict[Monster, str] = {}

    def register(self, monster: Monster) -> None:
        """Mark a monster as swapped in for this turn."""
        self._swapped_this_turn.add(monster)

    def block_swap(
        self,
        monster: Monster,
        reason: str = "unknown",
        persistent: bool = False,
    ) -> None:
        """Block swapping for a monster with a reason. Persistent blocks last across turns."""
        if persistent:
            self._persistent_blocked_swaps[monster] = reason
        else:
            self._temp_blocked_swaps[monster] = reason

    def unblock_swap(self, monster: Monster) -> None:
        """Remove any swap block, temporary or persistent."""
        self._temp_blocked_swaps.pop(monster, None)
        self._persistent_blocked_swaps.pop(monster, None)

    def clear(self) -> None:
        """Reset turn-specific swap state and temporary blocks."""
        self._swapped_this_turn.clear()
        self._temp_blocked_swaps.clear()

    def can_swap(self, monster: Monster) -> bool:
        """True if the monster hasn't swapped this turn and isn't blocked."""
        return (
            monster not in self._swapped_this_turn
            and monster not in self._temp_blocked_swaps
            and monster not in self._persistent_blocked_swaps
        )
