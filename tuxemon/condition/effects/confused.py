# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.combat import has_effect_param
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
    Confused status

    """

    name = "confused"

    def apply(self, tech: Condition, target: Monster) -> ConfusedEffectResult:
        extra: Optional[str] = None
        skip: Optional[Technique] = None
        player = self.session.player
        if tech.phase == "pre_checking":
            if tech.slug == "status_confused":
                confusion = random.randint(1, 1)
                if confusion == 1:
                    user = tech.link
                    assert user
                    player.game_variables["status_confused"] = "on"
                    confused = [
                        ele
                        for ele in user.moves
                        if ele.next_use <= 0
                        and not has_effect_param(
                            ele, "status_confused", "give", "condition"
                        )
                    ]
                    if confused:
                        skip = random.choice(confused)
                    else:
                        skip = Technique()
                        skip.load("empty")
                else:
                    player.game_variables["status_confused"] = "off"
        if tech.phase == "perform_action_tech":
            if tech.slug == "status_confused":
                if "status_confused" in player.game_variables:
                    if player.game_variables["status_confused"] == "on":
                        _tech = Technique()
                        _tech.load(player.game_variables["action_tech"])
                        extra = T.format(
                            "combat_state_confused_tech",
                            {
                                "target": target.name.upper(),
                                "name": _tech.name.upper(),
                            },
                        )
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": extra,
        }
