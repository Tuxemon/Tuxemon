# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.database.runtime import db

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class SwitchTypeEffect(CoreEffect):
    """
    Applies the "switch_type" effect to an item.

    This effect changes the elemental type of the target monster. The new
    type can be explicitly specified or chosen randomly from the available
    elements in the database. If the target already has the specified type,
    no change is applied.

    **Parameters**

    - ``element``: String representing the new type to assign.
      - Can be a specific element (e.g., ``wood``, ``water``).
      - Or ``random`` to select a random element from the database.

    **Examples**

    .. code-block:: json

        "effects": [
            "switch_type wood"
        ]

        "effects": [
            "switch_type random"
        ]
    """

    name = "switch_type"
    element: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        elements = list(db.database["element"])

        if self.element != "random":
            if not target.has_type(self.element):
                target.types.set_types([self.element])
        else:
            random_slug = random.choice(elements)
            target.types.set_types([random_slug])

        return ItemEffectResult(name=item.name, success=True)
