# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import has_status
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class RemoveEffectResult(TechEffectResult):
    pass


@dataclass
class RemoveEffect(TechEffect):
    """
    This effect has a chance to remove a status effect.
    "remove status_xxx,target" removes only status_xxx
    "remove all, target" removes everything
    """

    name = "remove"
    condition: str
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RemoveEffectResult:
        done: bool = False
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            if self.objective == "user":
                if self.condition == "all":
                    done = True
                    user.status.clear()
                else:
                    if has_status(user, self.condition):
                        done = True
                        target.status.clear()
            elif self.objective == "target":
                if self.condition == "all":
                    done = True
                    target.status.clear()
                else:
                    if has_status(target, self.condition):
                        done = True
                        target.status.clear()
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
