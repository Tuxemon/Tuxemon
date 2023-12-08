# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
        if self.statistic == StatType.hp:
            value = target.hp * self.percentage
            target.hp += int(value)
        elif self.statistic == StatType.armour:
            value = target.armour * self.percentage
            target.armour += int(value)
        elif self.statistic == StatType.dodge:
            value = target.dodge * self.percentage
            target.dodge += int(value)
        elif self.statistic == StatType.melee:
            value = target.melee * self.percentage
            target.melee += int(value)
        elif self.statistic == StatType.ranged:
            value = target.ranged * self.percentage
            target.ranged += int(value)
        elif self.statistic == StatType.speed:
            value = target.speed * self.percentage
            target.speed += int(value)
        else:
            raise ValueError(f"{self.statistic} must be a stat.")

        return {"success": True, "num_shakes": 0, "extra": None}
