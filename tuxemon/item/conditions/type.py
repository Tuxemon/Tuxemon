# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class TypeCondition(ItemCondition):
    """
    Compares the target Monster's type against the given types.

    Returns true if its equal to any of the listed types.

    """

    name = "type"
    elements: str

    def test(self, target: Monster) -> bool:
        ret: bool = False
        elements: list[str] = []
        if self.elements.find(":"):
            elements = self.elements.split(":")
        else:
            elements.append(self.elements)
        for ele in target.types:
            if ele.slug in elements:
                ret = True
        return ret
