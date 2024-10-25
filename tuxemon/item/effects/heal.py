# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.combat import has_status
from tuxemon.db import ItemCategory
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


@dataclass
class HealEffect(ItemEffect):
    """
    Heals the target by 'amount' hp.

    Parameters:
        amount: int or float, where:
            - int: constant amount of hp to heal
            - float: percentage of total hp to heal (e.g., 0.5 for 50%)
        heal_type: indicating whether the amount is a fixed value or a percentage

    Examples:
        heal 0.5 > heals 50% of target's total hp
    """

    name = "heal"
    amount: Union[int, float]
    heal_type: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        if not target:
            raise ValueError("Target cannot be None")

        category = ItemCategory.potion
        if has_status(target, "festering") and item.category == category:
            return ItemEffectResult(
                name=item.name,
                success=False,
                num_shakes=0,
                extra=[T.translate("combat_state_festering_item")],
            )

        if self.heal_type == "fixed":
            healing_amount = int(self.amount)
        elif self.heal_type == "percentage":
            healing_amount = int(target.hp * self.amount)
        else:
            raise ValueError(
                f"Invalid heal type '{self.heal_type}'. Must be either 'fixed' or 'percentage'."
            )
        target.current_hp = min(target.hp, target.current_hp + healing_amount)

        return ItemEffectResult(
            name=item.name, success=True, num_shakes=0, extra=[]
        )
