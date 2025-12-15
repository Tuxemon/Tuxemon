# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.core.core_condition import CoreCondition
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class CurrentHitPointsCondition(CoreCondition):
    """
    Compares the Monster's current hitpoints against a specified value.

    **Parameters**
    - ``operator``: The comparison operator (e.g. ``<``, ``>``, ``<=``, ``>=``).
    - ``hp``: The value to compare against. If an integer, compares directly to current HP.
    If a float between 0.0 and 1.0, compares the current HP against that fraction of total HP.

    **Returns**
    - ``True`` if the comparison evaluates successfully.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is current_hp <,1.0"
        ]
    """

    name = "current_hp"
    operator: str
    hp: Union[int, float]

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        value = target.hp * self.hp if type(self.hp) is float else self.hp
        return compare(self.operator, target.current_hp, value)
