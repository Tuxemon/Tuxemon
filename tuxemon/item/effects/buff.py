# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import StatType
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class BuffEffectResult(ItemEffectResult):
    pass


@dataclass
class BuffEffect(ItemEffect):
    """
    Increases or decreases target's stats by percentage temporarily.

    Parameters:
        statistic: type of statistic (hp, armour, etc.)
        percentage: percentage of the statistic (increase / decrease)

    """

    name = "buff"
    statistic: StatType
    percentage: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> BuffEffectResult:
        assert target

        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        amount = target.return_stat(StatType(self.statistic))
        value = int(amount * self.percentage)

        target.armour += value if self.statistic == StatType.armour else 0
        target.dodge += value if self.statistic == StatType.dodge else 0
        target.hp += value if self.statistic == StatType.hp else 0
        target.melee += value if self.statistic == StatType.melee else 0
        target.speed += value if self.statistic == StatType.speed else 0
        target.ranged += value if self.statistic == StatType.ranged else 0

        return {"success": True, "num_shakes": 0, "extra": None}
