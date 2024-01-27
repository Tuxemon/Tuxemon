# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.combat import has_effect_param, recharging
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class ConfusedEffectResult(CondEffectResult):
    pass


@dataclass
class ConfusedEffect(CondEffect):
    """
    Confused: Instead of the technique chosen, the Confused monster uses a
    random technique (from the ones they have available, other than the one
    chosen) 50% of the time.

    Parameters:
        chance: The chance.

    """

    name = "confused"
    chance: float

    def apply(
        self, condition: Condition, target: Monster
    ) -> ConfusedEffectResult:
        extra: Optional[str] = None
        skip: Optional[Technique] = None
        player = target.owner
        assert player
        if "confused" in player.game_variables:
            player.game_variables["confused"] = "off"
        if condition.phase == "pre_checking" and random.random() > self.chance:
            user = condition.link
            assert user
            player.game_variables["confused"] = "on"
            confused = [
                ele
                for ele in user.moves
                if not recharging(ele)
                and not has_effect_param(ele, "confused", "give", "condition")
            ]
            if confused:
                skip = random.choice(confused)
            if not confused and condition.repl_tech:
                skip = Technique()
                skip.load(condition.repl_tech)
        if (
            condition.phase == "perform_action_tech"
            and player.game_variables["confused"] == "on"
        ):
            _tech = Technique()
            _tech.load(player.game_variables["action_tech"])
            params = {
                "target": target.name.upper(),
                "name": _tech.name.upper(),
            }
            extra = T.format("combat_state_confused_tech", params)
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": extra,
        }
