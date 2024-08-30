# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.combat import has_status, set_var
from tuxemon.db import ItemCategory
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class HealEffectResult(ItemEffectResult):
    pass


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
    ) -> HealEffectResult:
        if not target:
            raise ValueError("Target cannot be None")

        category = ItemCategory.potion
        if has_status(target, "festering") and item.category == category:
            return {
                "success": False,
                "num_shakes": 0,
                "extra": T.translate("combat_state_festering_item"),
            }

        if self.heal_type == "fixed":
            healing_amount = int(self.amount)
        elif self.heal_type == "percentage":
            healing_amount = int(target.hp * self.amount)
        else:
            raise ValueError(
                f"Invalid heal type '{self.heal_type}'. Must be either 'fixed' or 'percentage'."
            )

        set_var(self.session, self.name, str(target.instance_id.hex))
        client = self.session.client.event_engine
        params = [self.name, healing_amount]
        client.execute_action("modify_monster_health", params, True)

        return {"success": True, "num_shakes": 0, "extra": None}
