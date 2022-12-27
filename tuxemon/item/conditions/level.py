# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from operator import eq, ge, gt, le, lt
from typing import Callable, Mapping, Optional

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster

cmp_dict: Mapping[Optional[str], Callable[[float, float], bool]] = {
    None: ge,
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
    "==": eq,
    "=": eq,
}


@dataclass
class LevelCondition(ItemCondition):
    """
    Compares the target Monster's level against the given value.

    Example: To make an item only usable if a monster is at a
    certain level, you would use the condition "level target,<,5"

    """

    name = "level"
    comparison: str
    value: int

    def test(self, target: Monster) -> bool:
        level = target.level
        operator = cmp_dict[self.comparison]
        level_reached = self.value

        return operator(level, level_reached)
