# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class CategoryCondition(ItemCondition):
    """
    Compares the target Monster's condition against the given condition.

    Returns true if its equal to any of the listed types.

    eg. "not category threat:bird"

    """

    name = "category"
    cat: str

    def test(self, target: Monster) -> bool:
        categories: list[str] = []
        if self.cat.find(":"):
            categories = self.cat.split(":")
        else:
            categories.append(self.cat)
        category = True if target.cat in categories else False
        return category
