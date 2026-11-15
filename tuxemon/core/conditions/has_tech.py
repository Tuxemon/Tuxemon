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
class HasTechCondition(CoreCondition):
    """
    Checks whether the target Monster already knows a specific technique.

    **Parameters**
    - ``expected``: The slug or name of the technique to check.

    **Returns**
    - ``True`` if the Monster has the given technique.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is has_tech tackle"
        ]
    """

    name = "has_tech"
    expected: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return target.moves.has_move(self.expected)
