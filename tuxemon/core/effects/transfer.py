# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class TransferEffect(CoreEffect):
    """
    Transfers a specified condition from one entity to another.

    The direction of the transfer is determined by the `direction` attribute,
    which can be either "user_to_target" or "target_to_user".
    If the source entity has the specified condition, it is removed from the
    source and applied to the target.
    """

    name = "transfer"
    condition: str
    direction: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        done = False
        if tech.hit:
            source, dest = (
                (user, target)
                if self.direction == "user_to_target"
                else (target, user)
            )
            if source.status.has_status(self.condition):
                dest.status = source.status
                source.status.clear_status()
                done = True
        return TechEffectResult(name=tech.name, success=done)
