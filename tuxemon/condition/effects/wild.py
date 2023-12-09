# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class WildEffectResult(CondEffectResult):
    pass


@dataclass
class WildEffect(CondEffect):
    """
    Wild status

    """

    name = "wild"

    def apply(self, condition: Condition, target: Monster) -> WildEffectResult:
        skip: Optional[Technique] = None
        if condition.phase == "pre_checking" and condition.slug == "wild":
            wild = random.randint(1, 4)
            if wild == 1:
                user = condition.link
                assert user
                skip = Technique()
                skip.load("empty")
                user.current_hp -= user.hp // 8
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": None,
        }
