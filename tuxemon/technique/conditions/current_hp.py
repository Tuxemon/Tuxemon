# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.technique.techcondition import TechCondition
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class CurrentHitPointsCondition(TechCondition):
    """
    Compares the Monster's current hitpoints against the given value.

    If an integer is passed, it will compare against the number directly, if a
    decimal between 0.0 and 1.0 is passed it will compare the current hp
    against the total hp.

    Parameters:
        operator: The operator <, >, etc.
        hp: The hp (int or float) to compare with.

    Example:
    "conditions": [
        "is current_hp <,1.0",
    ],

    """

    name = "current_hp"
    operator: str
    hp: Union[int, float]

    def test(self, target: Monster) -> bool:
        value = target.hp * self.hp if type(self.hp) is float else self.hp
        return compare(self.operator, target.current_hp, value)
