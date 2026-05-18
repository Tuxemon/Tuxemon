# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class BuffEffect(CoreEffect):
    """
    Temporarily increases or decreases a target's statistic by a percentage.

    **Parameters**

    - ``statistic``: The type of statistic to modify (e.g. ``hp``, ``armour``, ``speed``).
    - ``percentage``: The fraction of the statistic to apply as a buff or debuff.
      Positive values increase the stat, negative values decrease it.

    **Example**

    .. code-block:: json

        "effects": [
            "buff hp 0.25"
        ]
    """

    name = "buff"
    statistic: StatType
    percentage: float

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:

        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        current_value = target.return_stat(self.statistic)
        boost_value = int(current_value * self.percentage)
        stat_name = self.statistic.value  # e.g. "speed", "armour", etc.
        setattr(item.temporary_stat_boosts, stat_name, boost_value)
        return ItemEffectResult(name=item.name, success=True)
