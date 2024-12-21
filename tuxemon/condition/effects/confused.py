# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import has_effect_param, recharging
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class ConfusedEffect(CondEffect):
    """
    Confused: Instead of the technique chosen, the Confused monster uses a
    random technique (from the ones they have available, other than the one
    chosen) 50% of the time.

    Parameters:
        chance: The chance of the confused effect occurring (float between 0 and 1).

    """

    name = "confused"
    chance: float

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        CONFUSED_KEY = self.name

        if not _validate_chance(self.chance):
            raise ValueError("Chance must be a float between 0 and 1")

        extra: list[str] = []
        tech: list[Technique] = []
        combat = condition.combat_state
        assert combat
        if CONFUSED_KEY in combat._combat_variables:
            combat._combat_variables[CONFUSED_KEY] = "off"

        if condition.phase == "pre_checking" and random.random() > self.chance:
            user = condition.link
            assert user
            combat._combat_variables[CONFUSED_KEY] = "on"
            available_techniques = _get_available_techniques(user)
            if available_techniques:
                chosen_technique = random.choice(available_techniques)
                tech = [chosen_technique]
            elif condition.repl_tech:
                replacement_technique = Technique()
                replacement_technique.load(condition.repl_tech)
                tech = [replacement_technique]

        if (
            condition.phase == "perform_action_tech"
            and combat._combat_variables[CONFUSED_KEY] == "on"
        ):
            replacement = Technique()
            slug = combat._combat_variables.get("action_tech", "skip")
            replacement.load(slug)
            extra = _get_extra_message(target, replacement)

        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=tech,
            extras=extra,
        )


def _validate_chance(chance: float) -> bool:
    return 0 <= chance <= 1


def _get_available_techniques(user: Monster) -> list[Technique]:
    return [
        move
        for move in user.moves
        if not recharging(move)
        and not has_effect_param(move, "confused", "give", "condition")
    ]


def _get_extra_message(target: Monster, technique: Technique) -> list[str]:
    params = {
        "target": target.name.upper(),
        "name": technique.name.upper(),
    }
    return [T.format("combat_state_confused_tech", params)]
