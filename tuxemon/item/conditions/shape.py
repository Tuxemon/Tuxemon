# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class ShapeCondition(ItemCondition):
    """
    Compares the target Monster's shape against the given types.

    Returns true if its equal to any of the listed types.

    """

    name = "shape"
    shape1: str
    shape2: Union[str, None] = None
    shape3: Union[str, None] = None
    shape4: Union[str, None] = None
    shape5: Union[str, None] = None

    def test(self, target: Monster) -> bool:
        ret = False
        if target.shape is not None:
            ret = any(
                target.shape.lower() == p.lower()
                for p in self.shape1
                if p is not None
            )

        return ret
