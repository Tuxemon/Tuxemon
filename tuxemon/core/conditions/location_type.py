# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.map.manager import MAP_TYPES

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class LocationTypeCondition(CoreCondition):
    """
    Checks whether the player's current location type matches a specified category.

    **Parameters**
    - ``location_type``: The type of location to check (must be one of the defined MAP_TYPES).

    **Returns**
    - ``True`` if the player's current location matches the given type.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is location_type cave"
        ]
    """

    name = "location_type"
    location_type: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return (
            self.location_type in MAP_TYPES
            and session.client.map_manager.is_in_location_type(
                self.location_type
            )
        )
