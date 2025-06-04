# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class WildEffect(CoreEffect):
    """
    Wild: 1/4 chance each turn that instead of using the chosen
    technique, you take 1/8 your maximum HP in unmodified damage.

    Parameters:
        chance: The chance.
        divisor: The divisor.

    """

    name = "wild"
    chance: float
    divisor: int

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        tech: list[Technique] = []
        if status.phase == "pre_checking" and random.random() > self.chance:
            user = status.link
            empty = status.repl_tech
            assert user and empty
            skip = Technique.create(empty)
            tech = [skip]
            if not user.is_fainted:
                damage = user.hp // self.divisor
                user.current_hp = max(0, user.current_hp - damage)
        return StatusEffectResult(
            name=status.name, success=True, techniques=tech
        )
