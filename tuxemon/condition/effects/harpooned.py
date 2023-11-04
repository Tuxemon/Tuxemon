# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class HarpoonedEffectResult(CondEffectResult):
    pass


@dataclass
class HarpoonedEffect(CondEffect):
    """
    Status harpooned.

    """

    name = "harpooned"

    def apply(self, tech: Condition, target: Monster) -> HarpoonedEffectResult:
        if tech.phase == "add_monster_into_play":
            if tech.slug == "harpooned":
                target.current_hp -= target.hp // 8
                if target.current_hp <= 0:
                    target.faint()
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
