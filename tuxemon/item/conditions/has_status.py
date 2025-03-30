# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
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
        "is has_status xxx"
    ],

    """

    name = "has_status"

    def test(self, target: Monster) -> bool:
        if target.status:
            return True
        else:
            return False
