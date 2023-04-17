# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class RecoverEffectResult(TechEffectResult):
    pass


@dataclass
class RecoverEffect(TechEffect):
    """
    This effect has a chance to apply the recovering status effect.
    """

    name = "recover"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RecoverEffectResult:
        if tech.slug == "status_recover":
            # avoids Nonetype situation and reset the user
            if user is None:
                user = tech.link
                assert user
                heal = formula.simple_recover(user)
                user.current_hp += heal
            else:
                heal = formula.simple_recover(user)
                user.current_hp += heal

            return {
                "success": bool(heal),
            }

        return {"success": False}
