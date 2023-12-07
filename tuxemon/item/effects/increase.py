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


class IncreaseEffectResult(ItemEffectResult):
    pass


@dataclass
class IncreaseEffect(ItemEffect):
    """
    Increases or decreases target's stats by percentage permanently.

    Parameters:
        statistic: type of statistic (hp, armour, etc.)
        percentage: percentage of the statistic (increase / decrease)

    """

    name = "increase"
    statistic: StatType
    percentage: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> IncreaseEffectResult:
        assert target
        if self.statistic == StatType.hp:
            value = target.hp * self.percentage
            target.mod_hp += int(value)
        elif self.statistic == StatType.armour:
            value = target.armour * self.percentage
            target.mod_armour += int(value)
        elif self.statistic == StatType.dodge:
            value = target.dodge * self.percentage
            target.mod_dodge += int(value)
        elif self.statistic == StatType.melee:
            value = target.melee * self.percentage
            target.mod_melee += int(value)
        elif self.statistic == StatType.ranged:
            value = target.ranged * self.percentage
            target.mod_ranged += int(value)
        elif self.statistic == StatType.speed:
            value = target.speed * self.percentage
            target.mod_speed += int(value)
        else:
            raise ValueError(f"{self.statistic} must be a stat.")
        target.set_stats()
        return {"success": True, "num_shakes": 0, "extra": None}
