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
class CurrentStatusCondition(CoreCondition):
    """
    Checks whether the target Monster currently has a specific status effect.

    **Parameters**
    - ``expected``: The slug of the status to check for (e.g. ``poisoned``, ``sleep``).

    **Returns**
    - ``True`` if the Monster has the given status.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is status poisoned"
        ]
    """

    name = "status"
    expected: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return any(
            self.expected == x.slug for x in target.status.get_statuses()
        )
