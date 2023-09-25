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


class PoisonedEffectResult(CondEffectResult):
    pass


@dataclass
class PoisonedEffect(CondEffect):
    """
    This effect has a chance to apply the poisoned status.
    """

    name = "poisoned"

    def apply(self, tech: Condition, target: Monster) -> PoisonedEffectResult:
        poisoned: bool = False
        if tech.phase == "perform_action_status":
            if tech.slug == "poison":
                damage = formula.damage_full_hp(target, 8)
                target.current_hp -= damage
                poisoned = True

        return {
            "success": poisoned,
            "condition": None,
            "technique": None,
            "extra": None,
        }
