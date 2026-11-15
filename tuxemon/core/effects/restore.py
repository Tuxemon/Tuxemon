# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import CategoryStatus

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class RestoreEffect(CoreEffect):
    """
    Applies the "restore" effect to an item.

    This effect removes one or more status effects from the target monster.
    It can clear all statuses, or selectively remove only positive or
    negative statuses depending on the specified category.

    **Parameters**

      - ``category``: Determines which statuses to remove.
      - ``None``: Removes all statuses.
      - ``positive``: Removes only positive statuses.
      - ``negative``: Removes only negative statuses.

    **Examples**

    .. code-block:: json

        "effects": [
            "restore"
        ]

        "effects": [
            "restore positive"
        ]

        "effects": [
            "restore negative"
        ]
    """

    name = "restore"
    category: str | None = None

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.category:
            if (
                self.category == CategoryStatus.POSITIVE
                or self.category == CategoryStatus.NEGATIVE
            ):
                checking = [
                    ele
                    for ele in target.status.get_statuses()
                    if ele.category == self.category
                ]
                # removes negative or positive statuses
                if checking:
                    target.status.clear_status(session)
                else:
                    pass
            else:
                raise ValueError(
                    f"{self.category} must be positive or negative."
                )
        else:
            target.status.clear_status(session)

        return ItemEffectResult(name=item.name, success=True)
