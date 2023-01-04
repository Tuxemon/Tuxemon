# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class HealEffectResult(ItemEffectResult):
    pass


@dataclass
class HealEffect(ItemEffect):
    """
    Heals the target by 'amount' hp.

    This is a constant if amount is an integer, a percentage of total hp
    if a float

    Examples:
    >>> potion = Item('potion')
    >>> potion.amount = 0.5
    >>> potion.apply(bulbatux)
    >>> # bulbatux is healed by 50% of it's total hp
    """

    name = "heal"
    amount: Union[int, float]

    def apply(self, target: Monster) -> HealEffectResult:
        healing_amount = self.amount
        if type(healing_amount) is float:
            healing_amount *= target.hp

        # Heal the target monster by "self.power" number of hitpoints.
        target.current_hp += int(healing_amount)

        # If we've exceeded the monster's maximum HP, set their health to 100%.
        if target.current_hp > target.hp:
            target.current_hp = target.hp

        return {"success": True}
