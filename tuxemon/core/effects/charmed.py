# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class CharmedEffect(CoreEffect):
    """
    Applies the "charmed" status to a monster.

    This effect introduces a chance for the monster's action to fail if it
    targets an opponent. By default, there is a 50% chance of failure, but
    the probability can be configured.

    **Parameters**

    - ``chance``: The probability of resisting the charm effect (between 0 and 1).
      Higher values reduce the likelihood of failure.

    **Example**

    .. code-block:: json

        "effects": [
            "charmed 0.5"
        ]
    """

    name = "charmed"
    chance: float

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        if (
            status.has_phase(EffectPhase.PRE_CHECKING)
            and random.random() > self.chance
        ):
            user = status.host
            action = session.client.combat_session.get_variable("action_tech")
            technique = Technique.create(str(action) or "skip")
            if any(
                technique.target.get(target_type, True)
                for target_type in [
                    "enemy_monster",
                    "enemy_team",
                    "enemy_trainer",
                ]
            ):
                session.client.combat_session.set_tech_hit(user, 1.1)


        if status.has_phase(EffectPhase.PERFORM_TECH):
            user = status.host
            hit = session.client.combat_session.get_tech_hit(user)
            if hit > 1.0:
                params = {"user": user.name}
                return StatusEffectResult(
                    name=status.name,
                    success=True,
                    extras=[T.format("combat_state_charmed_miss", params)],
                )

        return StatusEffectResult(name=status.name, success=True)
