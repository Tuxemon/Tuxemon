# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase, Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster.monster import Monster
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class RetaliateEffect(CoreEffect):
    """
    Applies the "retaliate" status effect.

    This effect causes the host monster to retaliate against attackers by
    accumulating damage taken between entering the retaliate state and the
    next time the host deals damage. The accumulated damage is then added
    to the host's next attack, dealing additional damage to the attacker.
    After the retaliatory strike, the accumulated damage is reset.

    **Example**

    .. code-block:: json

        "effects": [
            "retaliate"
        ]
    """

    name = "retaliate"

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host

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
            return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=False)
