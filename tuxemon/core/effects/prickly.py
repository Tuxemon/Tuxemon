# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.monster.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class PricklyBackEffect(CoreEffect):
    """
    Applies the "prickly" status effect.

    This effect causes attackers to take damage whenever they hit the host
    monster with a physical move. The damage dealt is equal to the host's
    maximum HP divided by the specified divisor. Only moves within the
    defined ranges trigger the effect.

    **Parameters**

    - ``divisor``: Integer value used to calculate the damage.
      - Damage is calculated as ``host.hp // divisor``.
    - ``ranges``: Colon-separated string of move ranges that trigger the effect
      (e.g., ``melee:ranged``).

    **Example**

    .. code-block:: json

        "effects": [
            "prickly 4 melee:ranged"
        ]
    """

    name = "prickly"
    divisor: int
    ranges: str

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
            and action.method.hit
            and action.method.range in self.ranges.split(":")
            and action.target.instance_id == host.instance_id
            and not action.user.is_fainted
        ):
            damage = host.hp // self.divisor
            action.user.current_hp = max(0, action.user.current_hp - damage)
            return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=False)
