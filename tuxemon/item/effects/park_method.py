# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.states.park.park import ParkState

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class ParkMethodEffectResult(ItemEffectResult):
    pass


@dataclass
class ParkMethodEffect(ItemEffect):
    """
    Park method increase or reduce the modifiers.

    park_method <doll>,<food>,<distance>

    both values are float (0 - 1)
    it accepts negative values too.

    eg: park_method 0.5,0,0
    eg: park_method -0.2,0.7,0
    """

    name = "park_method"
    doll: float
    food: float
    distance: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ParkMethodEffectResult:
        park = self.session.client.get_state_by_name(ParkState)
        if target and item.validate(target):
            park._food_modifier += self.food
            park._doll_modifier += self.doll
            park._distance += self.distance
        return {"success": True, "num_shakes": 0, "extra": None}
