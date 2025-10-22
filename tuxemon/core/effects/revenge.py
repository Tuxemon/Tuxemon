# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase, Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class RevengeEffect(CoreEffect):
    """
    Revenge:
    The next time you are attacked, the attacker takes the same amount of
    damage that you receive. Additionally, you heal for the amount of
    damage you dealt in the previous turn.

    Note: This effect is triggered only once, after which it is removed.
    """

    name = "revenge"

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.get_host()

        if not status.has_phase(EffectPhase.PERFORM_STATUS):
            return StatusEffectResult(name=status.name, success=False)

        combat = session.client.combat_session
        action = combat.action_queue.get_last_action(
            combat.turn, host, "target"
        )

        if (
            action
            and isinstance(action.method, Technique)
            and isinstance(action.user, Monster)
            and action.method.range != Range.special
            and action.method.hit
            and action.target.instance_id == host.instance_id
            and not action.user.is_fainted
        ):
            damage, _ = simple_damage_calculate(
                action.method, action.user, host
            )
            action.user.current_hp = max(0, action.user.current_hp - damage)
            host.current_hp = min(host.hp, host.current_hp + damage)
            return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=False)
