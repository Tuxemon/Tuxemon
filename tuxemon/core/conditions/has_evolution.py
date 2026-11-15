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
class HasEvolutionCondition(CoreCondition):
    """
    Checks whether the target Monster has an evolution ahead of it.

    Where ``can_evolve`` asks whether the Monster meets its evolution
    criteria right now, this asks only whether an evolution remains open to
    it at all, however far off.

    **Returns**

    - ``True`` if the Monster has an evolution it has not taken.
    - ``False`` if it is fully evolved, has no evolution paths, or has had
      them all blocked.

    **Example**

    .. code-block:: json

        "conditions": [
            "is has_evolution"
        ]
    """

    name = "has_evolution"

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return target.evolution_handler.has_pending_evolution()