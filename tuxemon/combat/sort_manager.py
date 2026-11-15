# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tuxemon.database.rules import config_combat
from tuxemon.formula import speed_monster
from tuxemon.monster.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.combat.action_queue import EnqueuedAction


@dataclass(order=True)
class ActionSortKey:
    primary_order: int
    speed: int
    tie_breaker: float = field(compare=True)


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
    def get_action_sort_key(cls, action: EnqueuedAction) -> ActionSortKey:
        """
        Compute and return the sort key used to determine this action's
        position in the turn order.

        The returned value is an ActionSortKey dataclass containing:
        - primary_order: An integer representing the action category's
          priority, based on its position in SORT_ORDER. Unknown categories
          are placed after all known ones.
        - speed: A secondary sort value representing the user's effective
          speed for this action. For most techniques this is determined by
          `speed_test()`. Certain action types (e.g., "meta", "potion")
          always use a speed of 0.
        - tie_breaker: A final float used to break ties between actions
          with identical primary and speed values. This typically comes
          from the action's `sub_priority`.

        If the action has no method or no user, a default key of
        ActionSortKey(0, 0, 0.0) is returned.
        """
        if action.method is None or action.user is None:
            return ActionSortKey(0, 0, 0.0)

        action_sort_type = action.method.sort
        primary = cls.get_sort_index(action_sort_type)

        if action_sort_type in ["meta", "potion"]:
            speed = 0
        else:
            speed = speed_test(action)

        tie = action.sub_priority

        return ActionSortKey(
            primary_order=primary,
            speed=speed,
            tie_breaker=tie,
        )


def speed_test(action: EnqueuedAction) -> int:
    """
    Calculate the speed modifier for the given action.
    """
    if isinstance(action.user, Monster) and isinstance(
        action.method, Technique
    ):
        return speed_monster(action.user, action.method)

    # NPCs using items, or Status effects, default to 0.
    # Their turn order is decided by Category (primary_order)
    # and then the Random Tie-breaker.
    return 0
