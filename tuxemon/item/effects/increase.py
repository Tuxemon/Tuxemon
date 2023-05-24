# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
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

    """

    name = "increase"
    stat: StatType
    amount: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> IncreaseEffectResult:
        assert target
        if self.stat == StatType.hp:
            value = target.hp * self.amount
            target.mod_hp += int(value)
        elif self.stat == StatType.armour:
            value = target.armour * self.amount
            target.mod_armour += int(value)
        elif self.stat == StatType.dodge:
            value = target.dodge * self.amount
            target.mod_dodge += int(value)
        elif self.stat == StatType.melee:
            value = target.melee * self.amount
            target.mod_melee += int(value)
        elif self.stat == StatType.ranged:
            value = target.ranged * self.amount
            target.mod_ranged += int(value)
        elif self.stat == StatType.speed:
            value = target.speed * self.amount
            target.mod_speed += int(value)
        else:
            logger.error(f"{self.stat} must be a stat.")
            raise ValueError()
        target.set_stats()
        logger.info(
            f"{target.name} {self.stat} has been increase by {int(value)}"
        )
        return {"success": True}
