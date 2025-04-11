# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.db import MapType

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class LocationTypeCondition(CoreCondition):
    """
    Checks against the location type the player's in.

    Shop, center, town, route, dungeon or notype.

    """

    name = "location_type"
    location_type: str

    def test_with_monster(self, target: Monster) -> bool:
        types = [maps.value for maps in MapType]
        return (
            self.location_type in types
            and self.session.client.map_type == self.location_type
        )
