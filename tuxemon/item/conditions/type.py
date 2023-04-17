# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class TypeCondition(ItemCondition):
    """
    Compares the target Monster's types[0] and types[1] against the given types.

    Returns true if either is equal to any of the listed types.

    """

    name = "type"
    type1: str
    type2: Union[str, None] = None
    type3: Union[str, None] = None
    type4: Union[str, None] = None
    type5: Union[str, None] = None

    def test(self, target: Monster) -> bool:
        ret = False
        if target.types[0] is not None:
            ret = any(
                target.types[0] == p
                for p in (
                    self.type1,
                    self.type2,
                    self.type3,
                    self.type4,
                    self.type5,
                )
                if p is not None
            )
        if len(target.types) > 1:
            ret = ret or any(
                target.types[1] == p
                for p in (
                    self.type1,
                    self.type2,
                    self.type3,
                    self.type4,
                    self.type5,
                )
                if p is not None
            )

        return ret
