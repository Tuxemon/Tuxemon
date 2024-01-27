# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class FesteringEffectResult(CondEffectResult):
    pass


@dataclass
class FesteringEffect(CondEffect):
    """
    This effect has a chance to apply the festering status effect.
    """

    name = "festering"

    def apply(
        self, condition: Condition, target: Monster
    ) -> FesteringEffectResult:
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
