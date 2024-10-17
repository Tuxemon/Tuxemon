# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import PlagueType
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PlagueEffectResult(TechEffectResult):
    pass


@dataclass
class PlagueEffect(TechEffect):
    """
    Plague is an effect that can infect a monster with a specific disease,
    with a configurable spreadness.

    Attributes:
        plague_slug: The slug of the plague to apply.
        spreadness: The chance of the plague spreading to the target monster.
    """

    name = "plague"
    plague_slug: str
    spreadness: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PlagueEffectResult:

        if random.random() < self.spreadness and (
            self.plague_slug not in target.plague
            or target.plague[self.plague_slug] != PlagueType.inoculated
        ):
            target.plague[self.plague_slug] = PlagueType.infected
            success = True
        else:
            success = False

        params = {"target": target.name.upper()}
        plague_status = target.plague.get(self.plague_slug, None)
        extra = T.format(
            (
                "combat_state_plague3"
                if plague_status == PlagueType.infected
                else "combat_state_plague0"
            ),
            params,
        )

        return {
            "success": success,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
