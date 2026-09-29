# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.database.rules import config_monster
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class HasTpRoomCondition(CoreCondition):
    """
    Checks whether a monster can still gain training points (TP) for a stat.

    The check passes only when the monster is below *both* training limits
    defined in the monster rules: the per-stat cap (``max_tps``) for the given
    statistic *and* the overall cap (``max_total_tps``) across all stats. If
    either cap is already reached, the condition fails, which makes TP-granting
    items (e.g. the ``raise_*`` items) ineligible for use on that monster.

    **Parameters**

    - ``statistic``: The statistic to check (e.g. ``hp``, ``armour``, ``speed``).

    **Returns**

    - ``True`` if the stat is below its per-stat cap and the total is below the
      overall cap.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is has_tp_room armour"
        ]
    """

    name = "has_tp_room"
    statistic: StatType

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        training_points = target.training_points
        stat_value = getattr(training_points, self.statistic.value)
        total_value = training_points.sum()

        return (
            stat_value < config_monster.max_tps
            and total_value < config_monster.max_total_tps
        )
