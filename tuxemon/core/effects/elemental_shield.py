# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class ElementalShieldBackEffect(CoreEffect):
    """
    Elemental Shield:
    Each time you are hit by a Special move the attacker takes damage equal to
    your maximum HP divided by the divisor.

    Parameters:
        divisor: The divisor used to calculate the damage.
        ranges: The ranges of moves that trigger the effect.
    """

    name = "elemental_shield"
    divisor: int
    ranges: str

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:

        if not status.has_phase(EffectPhase.PERFORM_STATUS):
            return StatusEffectResult(name=status.name, success=False)

        combat = session.client.combat_session
        action = combat.action_queue.get_last_action(
            combat.turn, target, "target"
        )

        if (
            action
            and isinstance(action.method, Technique)
            and isinstance(action.user, Monster)
            and action.method.hit
            and action.method.range in self.ranges.split(":")
            and action.target.instance_id == target.instance_id
            and not action.user.is_fainted
        ):
            damage = target.hp // self.divisor
            action.user.current_hp = max(0, action.user.current_hp - damage)
            return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=False)
