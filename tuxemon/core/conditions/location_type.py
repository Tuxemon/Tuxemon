# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.map_manager import map_types_list

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class LocationTypeCondition(CoreCondition):
    """
    Determines whether the player's current location type matches a
    specified category.
    """

    name = "location_type"
    location_type: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return (
            self.location_type in map_types_list
            and session.client.map_manager.is_in_location_type(
                self.location_type
            )
        )
