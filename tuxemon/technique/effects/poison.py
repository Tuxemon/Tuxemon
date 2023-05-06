# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PoisonEffectResult(TechEffectResult):
    pass


@dataclass
class PoisonEffect(TechEffect):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"

    def apply(
        self,
        tech: Technique,
        user: Union[Monster, None],
        target: Union[Monster, None],
    ) -> PoisonEffectResult:
        if tech.slug == "status_poison" and target:
            damage = formula.simple_poison(target)
            target.current_hp -= damage

            return {
                "success": bool(damage),
            }

        return {"success": False}
