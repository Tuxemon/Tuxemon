# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class LocationInsideCondition(ItemCondition):
    """
    Checks against the location type the player's in.

    Accepts "inside" or "outside"

    """

    name = "location_inside"
    location_inside: str

    def test(self, target: Monster) -> bool:
        if self.location_inside == "inside":
            if self.session.client.map_inside:
                return True
            else:
                return False
        elif self.location_inside == "outside":
            if self.session.client.map_inside:
                return False
            else:
                return True
        else:
            return False
