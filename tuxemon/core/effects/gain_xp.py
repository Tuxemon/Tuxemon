# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.utils import set_var
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class GainXpEffect(CoreEffect):
    """
    Applies the "gain_xp" effect to a monster.

    This effect increases the target monster's experience points by the
    specified amount when triggered by an item.

    **Parameters**

    - ``amount``: The amount of experience to add (integer).

    **Example**

    .. code-block:: json

        "effects": [
            "gain_xp 50"
        ]
    """

    name = "gain_xp"
    amount: int

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        set_var(session, self.name, target.instance_id.hex)
        client = session.client.event_engine
        _params = [self.name, self.amount, "true"]
        client.execute_action("give_experience", _params, True)
        return ItemEffectResult(name=item.name, success=True)
