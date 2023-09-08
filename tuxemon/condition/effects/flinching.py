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


class FlinchingEffectResult(CondEffectResult):
    pass


@dataclass
class FlinchingEffect(CondEffect):
    """
    Flinching status

    """

    name = "flinching"

    def apply(self, tech: Condition, target: Monster) -> FlinchingEffectResult:
        skip: Optional[Technique] = None
        if tech.phase == "pre_checking":
            if tech.slug == "status_flinching":
                fli = random.randint(1, 2)
                if fli == 1:
                    user = tech.link
                    assert user
                    skip = Technique()
                    skip.load("empty")
                    user.status.clear()
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": None,
        }
