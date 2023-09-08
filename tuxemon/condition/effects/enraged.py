# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class EnragedEffectResult(CondEffectResult):
    pass


@dataclass
class EnragedEffect(CondEffect):
    """
    Enraged status

    """

    name = "enraged"

    def apply(self, tech: Condition, target: Monster) -> EnragedEffectResult:
        if tech.phase == "perform_action_tech":
            if tech.slug == "status_enraged":
                target.status.clear()
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
