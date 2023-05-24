# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class DrainEffectResult(TechEffectResult):
    pass


@dataclass
class DrainEffect(TechEffect):
    """
    This effect has a chance to apply the drain status effect.
    Like poison, burn, etc.
    """

    name = "drain"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DrainEffectResult:
        drained: bool = False
        if tech.slug == "status_poison":
            damage = formula.damage_full_hp(target, 8)
            target.current_hp -= damage
            drained = True
        if tech.slug == "status_burn":
            damage = formula.damage_full_hp(target, 8)
            target.current_hp -= damage
            drained = True

        return {"success": drained}
