# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class ShapeCondition(ItemCondition):
    """
    Compares the target Monster's shape against the given types.

    Returns true if its equal to any of the listed types.

    """

    name = "shape"
    shapes: str

    def test(self, target: Monster) -> bool:
        shapes: list[str] = []
        if self.shapes.find(":"):
            shapes = self.shapes.split(":")
        else:
            shapes.append(self.shapes)
        if target.shape in shapes:
            return True
        else:
            return False
