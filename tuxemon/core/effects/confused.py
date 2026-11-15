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
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class ConfusedEffect(CoreEffect):
    """
    Applies the "confused" status to a monster.

    This effect causes the monster to sometimes ignore its chosen technique
    and instead use a random alternative. By default, there is a 50% chance
    of confusion occurring, but the probability can be configured.

    **Parameters**

    - ``chance``: The probability of the confused effect occurring (float between 0 and 1).
      Higher values increase the likelihood of confusion.

    **Example**

    .. code-block:: json

        "effects": [
            "confused 0.5"
        ]
    """

    name = "confused"
    chance: float

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:

        host = status.host

        if not 0 <= self.chance <= 1:
            raise ValueError(f"{self.chance} must be between 0 and 1")

        extra: list[str] = []
        tech: list[Technique] = []

        if status.has_phase(EffectPhase.PRE_CHECKING):
            if random.random() < self.chance:
                host.is_confused = True

                available = _get_available_techniques(host)
                if available:
                    tech = [random.choice(available)]
                elif status.on_tech_use:
                    tech = [Technique.create(status.on_tech_use)]
            else:
                host.is_confused = False

        if status.has_phase(EffectPhase.PERFORM_TECH) and host.is_confused:
            action = session.client.combat_session.get_variable("action_tech")
            replacement = Technique.create(str(action) or "skip")
            extra = _get_extra_message(host, replacement)
            host.is_confused = False

        return StatusEffectResult(
            name=status.name,
            success=True,
            techniques=tech,
            extras=extra,
        )


def _get_available_techniques(user: Monster) -> list[Technique]:
    return [
        move
        for move in user.moves.get_moves()
        if not move.is_recharging
        and not move.has_effect_param("give", "confused")
    ]


def _get_extra_message(target: Monster, technique: Technique) -> list[str]:
    params = {
        "target": target.name.upper(),
        "name": technique.name.upper(),
    }
    return [T.format("combat_state_confused_tech", params)]
