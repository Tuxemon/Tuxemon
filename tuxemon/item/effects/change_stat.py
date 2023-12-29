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
class ChangeStatEffect(ItemEffect):
    """
    Increases or decreases target's stats by percentage permanently.

    Parameters:
        statistic: type of statistic (hp, armour, etc.)
        percentage: percentage of the statistic (increase / decrease)

    """

    name = "change_stat"
    statistic: str
    percentage: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> IncreaseEffectResult:
        client = self.session.client
        assert target

        if self.statistic not in list(StatType):
            ValueError(f"{self.statistic} isn't among {list(StatType)}")

        var = f"{self.name}:{str(target.instance_id.hex)}"
        client.event_engine.execute_action("set_variable", [var], True)
        client.event_engine.execute_action(
            "modify_monster_stats",
            [self.name, self.statistic, self.percentage],
            True,
        )
        return {"success": True, "num_shakes": 0, "extra": None}
