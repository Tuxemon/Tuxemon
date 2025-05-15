# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class LocationInsideCondition(CoreCondition):
    """
    Checks against the location type the player's in.

    Accepts "inside" or "outside"

    """

    name = "location_inside"
    location_inside: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        if self.location_inside == "inside":
            return session.client.map_manager.map_inside
        elif self.location_inside == "outside":
            return not session.client.map_manager.map_inside
        return False
