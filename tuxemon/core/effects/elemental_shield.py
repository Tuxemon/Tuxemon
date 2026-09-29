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
class ElementalShieldBackEffect(CoreEffect):
    """
    Applies the "elemental shield" status to a monster.

    This effect reflects damage back to the attacker whenever the host is hit
    by a qualifying Special move. The reflected damage is equal to the host's
    maximum HP divided by the specified divisor.

    **Parameters**

    - ``divisor``: The divisor used to calculate reflected damage.
    - ``ranges``: A colon-separated string of move ranges that trigger the effect
      (e.g. ``"short:long"``).

    **Example**

    .. code-block:: json

        "effects": [
            "elemental_shield 4 short:long"
        ]
    """

    name = "elemental_shield"
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
