# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import has_status
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class TransferEffectResult(TechEffectResult):
    pass


@dataclass
class TransferEffect(TechEffect):
    """
    Transfers the condition from the user to the target.

    If the user has the condition, they lose that condition and the target
    gains it.
    """

    name = "transfer"
    condition: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TransferEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        done = False
        if tech.hit and has_status(user, self.condition):
            target.status = user.status
            user.status = []
            done = True
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
