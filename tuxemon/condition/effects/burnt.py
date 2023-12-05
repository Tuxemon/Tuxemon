# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class BurntEffectResult(CondEffectResult):
    pass


@dataclass
class BurntEffect(CondEffect):
    """
    This effect has a chance to apply the burnt status.
    """

    name = "burnt"

    def apply(
        self, condition: Condition, target: Monster
    ) -> BurntEffectResult:
        burnt: bool = False
        if (
            condition.phase == "perform_action_status"
            and condition.slug == "burn"
        ):
            damage = formula.damage_full_hp(target, 8)
            target.current_hp -= damage
            burnt = True

        return {
            "success": burnt,
            "condition": None,
            "technique": None,
            "extra": None,
        }
