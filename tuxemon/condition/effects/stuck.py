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


class StuckEffectResult(CondEffectResult):
    pass


@dataclass
class StuckEffect(CondEffect):
    """
    This effect has a chance to apply the stuck status effect.
    """

    name = "stuck"

    def apply(
        self, condition: Condition, target: Monster
    ) -> StuckEffectResult:
        done: bool = False
        if (
            condition.phase == "perform_action_status"
            and condition.slug == "stuck"
        ):
            formula.simple_stuck(target)
            done = True
        return {
            "success": done,
            "condition": None,
            "technique": None,
            "extra": None,
        }
