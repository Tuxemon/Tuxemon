# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class GiveEffectResult(TechEffectResult):
    pass


@dataclass
class GiveEffect(TechEffect):
    """
    This effect has a chance to give a status effect.
    """

    name = "give"
    condition: str
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> GiveEffectResult:
        done: bool = False
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            status = Technique()
            status.load(self.condition)
            status.link = user
            if self.objective == "user":
                user.apply_status(status)
                done = True
            elif self.objective == "target":
                target.apply_status(status)
                done = True
            elif self.objective == "both":
                user.apply_status(status)
                target.apply_status(status)
                done = True
        return {"success": done}
