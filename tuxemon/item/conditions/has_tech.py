# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class HasTechCondition(ItemCondition):
    """
    Checks if the monster knows already the technique.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "has_tech"
    expected: str

    def test(self, target: Monster) -> bool:
        if any(t for t in target.moves if t.slug == self.expected):
            return True
        else:
            return False
