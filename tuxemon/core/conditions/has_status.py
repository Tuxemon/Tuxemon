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
class HasStatusCondition(CoreCondition):
    """
    Checks whether the target Monster currently has any status effect.

    **Returns**
    - ``True`` if the Monster has at least one status.
    - ``False`` if the Monster has no statuses.

    **Example**

    .. code-block:: json

        "conditions": [
            "is has_status"
        ]
    """

    name = "has_status"

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return bool(target.status)
