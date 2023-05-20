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


class BurnEffectResult(TechEffectResult):
    pass


@dataclass
class BurnEffect(TechEffect):
    """
    This effect has a chance to apply the burn status effect.
    """

    name = "burn"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> BurnEffectResult:
        if tech.slug == "status_burn":
            damage = formula.damage_full_hp(target, 8)
            target.current_hp -= damage

            return {
                "success": bool(damage),
            }

        return {"success": False}
