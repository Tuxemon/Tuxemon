# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class LevelCondition(ItemCondition):
    """
    Compares the target Monster's level against the given value.

    Parameters:
        operator: The operator ">", "<", etc.
        level: The level to compare with.

    Example: To make an item only usable if a monster is at a
    certain level, you would use the condition "is level target,<,5"

    """

    name = "level"
    operator: str
    level: int

    def test(self, target: Monster) -> bool:
        return compare(self.operator, target.level, self.level)
