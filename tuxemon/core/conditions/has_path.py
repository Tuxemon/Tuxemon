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
class HasPathCondition(CoreCondition):
    """
    Checks whether the target Monster has an evolution path that requires a specific item.

    **Parameters**
    - ``expected``: The slug of the item to check for in the Monster's evolution paths.

    **Returns**
    - ``True`` if any of the Monster's evolutions include the given item.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is has_path evolution_stone"
        ]
    """

    name = "has_path"
    expected: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return any(
            self.expected in (evo.item or {}) for evo in target.evolutions
        )
