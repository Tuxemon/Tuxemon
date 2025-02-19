# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import MapType
from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class LocationTypeCondition(ItemCondition):
    """
    Checks against the location type the player's in.

    Shop, center, town, route, dungeon or notype.

    """

    name = "location_type"
    location_type: str

    def test(self, target: Monster) -> bool:
        types = [maps.value for maps in MapType]
        if self.location_type in types:
            if self.session.client.map_type == self.location_type:
                return True
            else:
                return False
        else:
            return False
