# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class GainXpEffectResult(ItemEffectResult):
    pass


@dataclass
class GainXpEffect(ItemEffect):
    """
    Add exp to the target by 'amount'.
    """

    name = "gain_xp"
    amount: int

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> GainXpEffectResult:
        assert target
        target.give_experience(self.amount)
        return {"success": True}
