# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import StatType
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class BuffEffectResult(ItemEffectResult):
    pass


@dataclass
class BuffEffect(ItemEffect):
    """
    Increases or decreases target's stats by percentage temporarily.

    """

    name = "buff"
    stat: StatType
    amount: float

    def apply(self, target: Monster) -> BuffEffectResult:
        if self.stat == StatType.hp:
            value = target.hp * self.amount
            target.hp += int(value)
        elif self.stat == StatType.armour:
            value = target.armour * self.amount
            target.armour += int(value)
        elif self.stat == StatType.dodge:
            value = target.dodge * self.amount
            target.dodge += int(value)
        elif self.stat == StatType.melee:
            value = target.melee * self.amount
            target.melee += int(value)
        elif self.stat == StatType.ranged:
            value = target.ranged * self.amount
            target.ranged += int(value)
        elif self.stat == StatType.speed:
            value = target.speed * self.amount
            target.speed += int(value)
        else:
            raise ValueError(f"{self.stat} must be a stat.")

        return {"success": True}
