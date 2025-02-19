# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class StatusCondition(ItemCondition):
    """
    Checks against the creature's current statuses.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "status"
    expected: str

    def test(self, target: Monster) -> bool:
        return self.expected in [
            x.slug for x in target.status if hasattr(x, "slug")
        ]
