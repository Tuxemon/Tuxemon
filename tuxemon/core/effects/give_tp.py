# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class GiveTpEffect(CoreEffect):
    """
    Permanently grants a target training points (TP) for a given statistic.

    Unlike ``change_stat`` (which writes an unbounded custom stat boost), this
    effect routes through :meth:`Monster.give_tps`, so the grant respects the
    monster's natural training limits (per-stat and total TP caps defined in
    the monster rules). Once a cap is reached, further grants add nothing.

    **Parameters**

    - ``statistic``: The type of statistic to train (e.g. ``hp``, ``armour``,
      ``speed``).
    - ``amount``: The number of training points to grant.

    **Example**

    .. code-block:: json

        "effects": [
            "give_tp armour 50"
        ]
    """

    name = "give_tp"
    statistic: StatType
    amount: int

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        target.give_tps(self.statistic.value, self.amount)
        return ItemEffectResult(name=item.name, success=True)
