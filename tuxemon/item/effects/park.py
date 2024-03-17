# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.combat import set_var
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class ParkEffectResult(ItemEffectResult):
    pass


@dataclass
class ParkEffect(ItemEffect):
    """
    Handles the items used in the park.

    Parameters:
        method: capture, doll or food

    """

    name = "park"
    method: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ParkEffectResult:
        assert target

        if self.method == "capture":
            labels = [
                "spyder_park_afraid",
                "spyder_park_stare",
                "spyder_park_wander",
            ]
            label = random.choice(labels)
            set_var(self.session, item.slug, label)
        elif self.method == "doll":
            pass
        elif self.method == "food":
            pass
        else:
            raise ValueError(f"Must be capture, doll or food")

        return {"success": True, "num_shakes": 0, "extra": None}
