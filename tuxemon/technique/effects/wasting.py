# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class WastingEffectResult(TechEffectResult):
    pass


@dataclass
class WastingEffect(TechEffect):
    """
    Wasting: Take #/16 of your maximum HP in damage each turn
    where # = the number of turns that you have had this condition.
    """

    name = "wasting"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> WastingEffectResult:
        if tech.slug == "status_wasting":
            damage = (target.hp // 16) * tech.nr_turn
            target.current_hp -= damage

            return {
                "success": bool(damage),
            }

        return {"success": False}
