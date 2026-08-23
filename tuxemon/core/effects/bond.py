# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class BondEffect(CoreEffect):
    """
    Changes the target monster's bond by a fixed amount.

    Unlike ``food_preference``, the change ignores the monster's tastes, so
    every monster gains (or loses) the same amount. An int is an absolute
    change, a float is a fraction of the monster's current bond. Decreases stop
    at the bond floor of the monster's evolution stage, and the effect fails if
    the bond couldn't move at all (for instance a gain on a monster that already
    adores its trainer).

    **Parameters**

    - ``amount``: Bond to add, negative to remove.

    **Example**

    .. code-block:: json

        "effects": [
            "bond 10"
        ]
    """

    name = "bond"
    amount: int | float

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        handler = target.bond_handler
        floor = handler.get_effective_min_bond(target.stage)
        previous = handler.bond
        crossed = handler.change_bond(self.amount, floor)
        if crossed:
            logger.debug(f"{target.name} crossed bond milestones: {crossed}")
        return ItemEffectResult(
            name=item.name, success=handler.bond != previous
        )
