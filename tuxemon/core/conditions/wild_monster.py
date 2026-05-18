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
class WildMonsterCondition(CoreCondition):
    """
    Checks whether the target Monster is wild (not owned by a trainer).

    **Returns**
    - ``True`` if the Monster is wild.
    - ``False`` if the Monster is owned by a trainer.

    **Example**

    .. code-block:: json

        "conditions": [
            "is wild_monster"
        ]
    """

    name = "wild_monster"

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return target.wild
