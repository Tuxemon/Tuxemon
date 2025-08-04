# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class CharmedEffect(CoreEffect):
    """
    Charmed: 50% chance of failing if they target an opponent.

    Parameters:
        chance: The chance.
    """

    name = "charmed"
    chance: float

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        if (
            status.has_phase(EffectPhase.PRE_CHECKING)
            and random.random() > self.chance
        ):
            user = status.get_host()
            combat = status.get_combat_state()
            slug = combat._combat_variables.get("action_tech", "skip")
            technique = Technique.create(slug)
            if any(
                technique.target.get(target_type, True)
                for target_type in [
                    "enemy_monster",
                    "enemy_team",
                    "enemy_trainer",
                ]
            ):
                combat.set_tech_hit(user, 1.0)
        return StatusEffectResult(name=status.name, success=True)
