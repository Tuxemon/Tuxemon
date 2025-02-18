# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class ScopeEffect(TechEffect):
    """
    Scope: scan monster stats.

    """

    name = "scope"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        params = {
            "AR": target.armour,
            "DE": target.dodge,
            "ME": target.melee,
            "RD": target.ranged,
            "SD": target.speed,
        }
        extra = [T.format("combat_scope", params)]
        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=extra,
        )
