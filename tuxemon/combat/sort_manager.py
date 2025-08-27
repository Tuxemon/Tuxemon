# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.formula import config_combat, speed_monster
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.combat.action_queue import EnqueuedAction


class SortManager:
    SORT_ORDER = config_combat.sort_order

    @classmethod
    def get_sort_index(cls, action_sort_type: str) -> int:
        """Returns the index of the action sort type in the SORT_ORDER list."""
        try:
            return cls.SORT_ORDER.index(action_sort_type)
        except ValueError:
            return len(cls.SORT_ORDER)

    @classmethod
    def get_action_sort_key(cls, action: EnqueuedAction) -> tuple[int, int]:
        """
        Returns a tuple representing the sort key for the given action.

        The sort key is a tuple of two integers: the primary order and the
        secondary order. The primary order is determined by the action's sort
        type, and the secondary order is determined by the user's speed test
        result (if applicable).

        If the action's method is None, or if the action's user is None, the
        function returns a default sort key of (0, 0).
        """
        if action.method is None or action.user is None:
            return 0, 0

        action_sort_type = action.method.sort
        primary_order = cls.get_sort_index(action_sort_type)

        if action_sort_type in ["meta", "potion"]:
            return primary_order, 0
        else:
            return primary_order, -speed_test(action)


def speed_test(action: EnqueuedAction) -> int:
    """
    Calculate the speed modifier for the given action.
    """
    if isinstance(action.user, Monster):
        if isinstance(action.method, Technique):
            return speed_monster(action.user, action.method)
    if isinstance(action.user, NPC):
        return 10
    return 0
