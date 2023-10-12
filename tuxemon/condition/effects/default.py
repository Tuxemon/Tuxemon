# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class DefaultEffectResult(CondEffectResult):
    pass


@dataclass
class DefaultEffect(CondEffect):
    """
    Default allows conditions without effects to manifest.

    """

    name = "default"

    def apply(self, tech: Condition, target: Monster) -> DefaultEffectResult:
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
