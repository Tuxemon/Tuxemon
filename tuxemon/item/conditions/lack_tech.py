# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class LackTechCondition(ItemCondition):
    """
    Checks if the monster knows already the technique.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "lack_tech"
    expected: str

    def test(self, target: Monster) -> bool:
        if any(t for t in target.moves if t.slug == self.expected):
            return False
        else:
            return True
