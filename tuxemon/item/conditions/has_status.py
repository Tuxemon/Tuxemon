# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class HasStatusCondition(ItemCondition):
    """
    Checks if the creature has a status or not.

    Parameters:
    -

    Example:
    "conditions": [
        "is has_status"
        "is has_status"
    ],

    """

    name = "has_status"
    category: Union[str, None] = None

    def test(self, target: Monster) -> bool:
        if self.category:
            if self.category == "positive" or self.category == "negative":
                checking = [
                    ele
                    for ele in target.status
                    if ele.category == self.category
                ]
                if checking:
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"{self.category} must be positive or negative"
                )
        else:
            if target.status:
                return True
            else:
                return False
