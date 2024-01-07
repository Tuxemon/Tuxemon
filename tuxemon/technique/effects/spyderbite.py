# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import PlagueType
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class SpyderbiteEffectResult(TechEffectResult):
    pass


@dataclass
class SpyderbiteEffect(TechEffect):
    """
    spyderbite: plague that can infect other monsters.

    """

    name = "spyderbite"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SpyderbiteEffectResult:
        # infect mechanism
        if (
            user.plague == PlagueType.infected
            or user.plague == PlagueType.healthy
        ):
            target.plague = PlagueType.infected

        params = {"target": target.name.upper()}
        if target.plague == PlagueType.infected:
            extra = T.format("combat_state_plague3", params)
        else:
            extra = T.format("combat_state_plague0", params)

        return {
            "success": True,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
