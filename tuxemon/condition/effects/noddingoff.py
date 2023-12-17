# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class NoddingOffEffectResult(CondEffectResult):
    pass


@dataclass
class NoddingOffEffect(CondEffect):
    """
    This effect has a chance to apply the nodding off status effect.
    """

    name = "noddingoff"

    def apply(
        self, condition: Condition, target: Monster
    ) -> NoddingOffEffectResult:
        extra: Optional[str] = None
        skip: Optional[Technique] = None

        if (
            condition.phase == "pre_checking"
            and condition.slug == "noddingoff"
        ):
            skip = Technique()
            skip.load("empty")

        if (
            condition.phase == "perform_action_tech"
            and condition.slug == "noddingoff"
            and self.wake_up(condition)
        ):
            extra = T.format(
                "combat_state_dozing_end",
                {
                    "target": target.name.upper(),
                },
            )
            target.status.clear()
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": extra,
        }

    def wake_up(self, condition: Condition) -> bool:
        value = random.random()
        if condition.duration >= condition.nr_turn > 0 and value > 0.5:
            return True
        if condition.nr_turn > condition.duration:
            return True
        return False
