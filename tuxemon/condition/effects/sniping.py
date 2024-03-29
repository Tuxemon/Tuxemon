# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class SnipingEffectResult(CondEffectResult):
    pass


@dataclass
class SnipingEffect(CondEffect):
    """
    Sniping status

    """

    name = "sniping"

    def apply(
        self, condition: Condition, target: Monster
    ) -> SnipingEffectResult:
        if condition.phase == "perform_action_tech":
            target.status.clear()
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
