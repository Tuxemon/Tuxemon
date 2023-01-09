# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class EnragedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


@dataclass
class EnragedEffect(TechEffect):
    """
    This effect has a chance to apply the enraged status effect.
    """

    name = "enraged"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> EnragedEffectResult:
        obj = self.objective
        success = tech.potency >= random.random()
        if success:
            tech = Technique("status_enraged")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
