# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

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
        amount: this is a constant if amount is an integer,
        a percentage of total hp if a float

    Examples:
        heal 0.5 > is healed by 50% of it's total hp

    """

    name = "heal"
    amount: Union[int, float]

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> HealEffectResult:
        extra: Optional[str] = None
        assert target
        category = ItemCategory.potion
        # condition festering = no healing
        if has_status(target, "festering") and item.category == category:
            extra = T.translate("combat_state_festering_item")
        else:
            set_var(self.session, self.name, str(target.instance_id.hex))
            client = self.session.client.event_engine
            params = [self.name, self.amount]
            client.execute_action("set_monster_health", params, True)

        return {"success": True, "num_shakes": 0, "extra": extra}
