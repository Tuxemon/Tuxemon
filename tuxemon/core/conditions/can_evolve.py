# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class CanEvolveCondition(CoreCondition):
    """
    Checks whether the target Monster currently meets its evolution criteria.

    **Returns**
    - ``True`` if the Monster can evolve under its current state and context.
    - ``False`` if the Monster cannot evolve or has no evolution paths.

    **Example**

    .. code-block:: json

        "conditions": [
            "is can_evolve"
        ]
    """

    name = "can_evolve"

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        context = {
            "map_inside": session.client.map_manager.map_inside,
            "use_item": True,
        }
        return bool(
            target.evolution_handler.get_eligible_evolution_slug(context)
        )
