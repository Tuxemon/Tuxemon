# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import ItemCategory
from tuxemon.formula import set_health
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class HealEffect(CoreEffect):
    """
    Applies the "heal" effect to a monster.

    This effect restores the target's HP by either a fixed amount or a
    percentage of its maximum HP, depending on the specified heal type.
    Healing may be blocked if the monster is affected by the "festering"
    status and the item used is a potion.

    **Parameters**

    - ``amount``: Integer or float value.
      - If integer: constant HP to heal.
      - If float: percentage of total HP to heal (e.g. ``0.5`` for 50%).
    - ``heal_type``: Indicates whether the amount is ``fixed`` or
      ``percentage``.

    **Example**

    .. code-block:: json

        "effects": [
            "heal 0.5 percentage"
        ]
    """

    name = "heal"
    amount: int | float
    heal_type: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        category = ItemCategory.POTION
        if target.status.has_status("festering") and item.category == category:
            return ItemEffectResult(
                name=item.name,
                extras=[T.translate("combat_state_festering_item")],
            )

        value: int | float
        if self.heal_type == "fixed":
            value = int(self.amount)
        elif self.heal_type == "percentage":
            value = float(self.amount)
        else:
            raise ValueError(
                f"Invalid heal type '{self.heal_type}'. Must be either 'fixed' or 'percentage'."
            )
        set_health(target, value, adjust=True)
        if target.is_fainted:
            target.status.apply_faint(session, target)

        return ItemEffectResult(name=item.name, success=True)
