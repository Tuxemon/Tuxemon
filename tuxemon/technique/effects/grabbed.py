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


class GrabbedEffectResult(TechEffectResult):
    pass


@dataclass
class GrabbedEffect(TechEffect):
    """
    This effect has a chance to apply the grabbed status effect.
    """

    name = "grabbed"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> GrabbedEffectResult:
        done: bool = False
        if tech.slug == "status_grabbed":
            formula.simple_grabbed(target)
            done = True
        return {"success": done}
