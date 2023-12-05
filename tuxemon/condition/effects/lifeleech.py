# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class LifeLeechEffectResult(CondEffectResult):
    pass


@dataclass
class LifeLeechEffect(CondEffect):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The Monster object that used this condition.
        target: The Monster object that we are using this condition on.

    Returns:
        Dict summarizing the result.

    """

    name = "lifeleech"

    def apply(
        self, condition: Condition, target: Monster
    ) -> LifeLeechEffectResult:
        lifeleech: bool = False
        if (
            condition.phase == "perform_action_status"
            and condition.slug == "lifeleech"
        ):
            user = condition.link
            assert user
            damage = formula.simple_lifeleech(user, target)
            target.current_hp -= damage
            user.current_hp += damage
            lifeleech = True

        return {
            "success": lifeleech,
            "condition": None,
            "technique": None,
            "extra": None,
        }
