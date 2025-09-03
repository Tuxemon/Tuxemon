# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.utils import has_effect_param
from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class ConfusedEffect(CoreEffect):
    """
    Confused: Instead of the technique chosen, the Confused monster uses a
    random technique (from the ones they have available, other than the one
    chosen) 50% of the time.

    Parameters:
        chance: The chance of the confused effect occurring (float between 0 and 1).

    """

    name = "confused"
    chance: float

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        CONFUSED_KEY = self.name
        var = session.client.combat_session.get_variable(CONFUSED_KEY)

        if not 0 <= self.chance <= 1:
            raise ValueError(f"{self.chance} must be between 0 and 1")

        extra: list[str] = []
        tech: list[Technique] = []

        if (
            status.has_phase(EffectPhase.PRE_CHECKING)
            and random.random() > self.chance
        ):
            if var:
                session.client.combat_session.set_variable(CONFUSED_KEY, "off")
            user = status.get_host()
            session.client.combat_session.set_variable(CONFUSED_KEY, "on")
            available_techniques = _get_available_techniques(user)
            if available_techniques:
                chosen_technique = random.choice(available_techniques)
                tech = [chosen_technique]
            elif status.on_tech_use:
                replacement_technique = Technique.create(status.on_tech_use)
                tech = [replacement_technique]

        if status.has_phase(EffectPhase.PERFORM_TECH):
            if var:
                session.client.combat_session.set_variable(CONFUSED_KEY, "off")
            if var and str(var) == "on":
                action = session.client.combat_session.get_variable(
                    "action_tech"
                )
                replacement = Technique.create(str(action) or "skip")
                extra = _get_extra_message(target, replacement)

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
        and not has_effect_param(move, "give", "condition", "confused")
    ]


def _get_extra_message(target: Monster, technique: Technique) -> list[str]:
    params = {
        "target": target.name.upper(),
        "name": technique.name.upper(),
    }
    return [T.format("combat_state_confused_tech", params)]
