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


class GrabbedEffectResult(CondEffectResult):
    pass


@dataclass
class GrabbedEffect(CondEffect):
    """
    This effect has a chance to apply the grabbed status effect.
    """

    name = "grabbed"

    def apply(self, tech: Condition, target: Monster) -> GrabbedEffectResult:
        done: bool = False
        if tech.phase == "perform_action_status":
            if tech.slug == "status_grabbed":
                formula.simple_grabbed(target)
                done = True
        return {
            "success": done,
            "condition": None,
            "technique": None,
            "extra": None,
        }
