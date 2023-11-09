# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

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
        self, tech: Condition, target: Monster
    ) -> NoddingOffEffectResult:
        extra: Optional[str] = None
        skip: Optional[Technique] = None
        if tech.phase == "pre_checking":
            if tech.slug == "noddingoff":
                skip = Technique()
                skip.load("empty")
        if tech.phase == "perform_action_tech" and tech.nr_turn > 0:
            if tech.slug == "noddingoff":
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
