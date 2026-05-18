# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class CurrentHitPointsCondition(CoreCondition):
    """
    Compares the Monster's hit point ratio against a specified value.

    **Parameters**
    - ``operator``: The comparison operator (e.g. ``<``, ``>``, ``<=``, ``>=``).
    - ``hp``: A floating-point value between 0.0 and 1.0 representing the HP ratio
    to compare against. The Monster's HP ratio is defined as
    ``current_hp / max_hp``.

    **Returns**
    - ``True`` if the comparison evaluates successfully.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is current_hp <,0.5"
        ]

    This example checks whether the Monster is below 50% of its maximum HP.
    """

    name = "current_hp"
    operator: str
    hp: float

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return compare(self.operator, target.hp_ratio, self.hp)
