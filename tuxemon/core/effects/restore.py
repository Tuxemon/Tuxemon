# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import CategoryStatus

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class RestoreEffect(CoreEffect):
    """
    Remove status/statuses.

    Parameters:
        category: status's category (positive or negative)

    Examples:
        restore -> removes all statuses
        restore positive -> removes all positive statuses
        restore negative -> removes all negative statuses

    """

    name = "restore"
    category: Union[str, None] = None

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.category:
            if (
                self.category == CategoryStatus.positive
                or self.category == CategoryStatus.negative
            ):
                checking = [
                    ele
                    for ele in target.status
                    if ele.category == self.category
                ]
                # removes negative or positive statuses
                if checking:
                    target.status.clear()
                else:
                    pass
            else:
                raise ValueError(
                    f"{self.category} must be positive or negative."
                )
        else:
            target.status.clear()

        return ItemEffectResult(name=item.name, success=True)
