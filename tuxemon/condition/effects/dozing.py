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


class DozingEffectResult(CondEffectResult):
    pass


@dataclass
class DozingEffect(CondEffect):
    """
    Dozing status

    """

    name = "dozing"

    def apply(self, tech: Condition, target: Monster) -> DozingEffectResult:
        extra: Optional[str] = None
        skip: Optional[Technique] = None
        if tech.phase == "pre_checking":
            if tech.slug == "status_dozing":
                skip = Technique()
                skip.load("empty")
        if tech.phase == "perform_action_tech":
            if tech.slug == "status_dozing":
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
