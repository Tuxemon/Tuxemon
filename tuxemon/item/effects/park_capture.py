# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from math import sqrt
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.states.park.park import ParkState

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class ParkCaptureEffectResult(ItemEffectResult):
    pass


@dataclass
class ParkCaptureEffect(ItemEffect):
    """
    Attempts to capture the target.
    Related only to Park.
    """

    name = "park_capture"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ParkCaptureEffectResult:
        assert target
        park = self.session.client.get_state_by_name(ParkState)
        # The number of shakes that a tuxemon can do to escape.
        total_shakes = 4
        # The max catch rate.
        max_catch_rate = 255
        # In every shake a random number form [0-65536] will be produced.
        max_shake_rate = 65536
        # Constant used in shake_check calculations
        shake_constant = 524325

        food_modifier = park._food_modifier
        doll_modifier = park._doll_modifier

        catch_check = (
            (3 * target.hp - 2 * target.current_hp)
            * target.catch_rate
            * food_modifier
            * doll_modifier
            / (3 * target.hp)
        )
        shake_check = shake_constant / (
            sqrt(sqrt(max_catch_rate / catch_check)) * 8
        )
        # Catch_resistance is a randomly generated number between the lower and upper catch_resistance of a tuxemon.
        # This value is used to slightly increase or decrease the chance of a tuxemon being caught. The value changes
        # Every time a new capture device is thrown.
        catch_resistance = random.uniform(
            target.lower_catch_resistance, target.upper_catch_resistance
        )
        # Catch_resistance is applied to the shake_check
        shake_check = shake_check * catch_resistance

        # 4 shakes to give monster chance to escape
        for i in range(0, total_shakes):
            random_num = random.randint(0, max_shake_rate)
            if random_num > round(shake_check):
                return {"success": False, "num_shakes": i + 1, "extra": None}

        # add creature to the player's monster list
        target.capture_device = item.slug
        self.user.add_monster(target, len(self.user.monsters))

        return {"success": True, "num_shakes": 4, "extra": None}
