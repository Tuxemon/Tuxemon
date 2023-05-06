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


class LifeLeechEffectResult(TechEffectResult):
    pass


@dataclass
class LifeLeechEffect(TechEffect):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "lifeleech"

    def apply(
        self,
        tech: Technique,
        user: Union[Monster, None],
        target: Union[Monster, None],
    ) -> LifeLeechEffectResult:
        if tech.slug == "status_lifeleech" and target:
            # avoids Nonetype situation and reset the user
            if user is None:
                user = tech.link
                assert user
                damage = formula.simple_lifeleech(user, target)
                target.current_hp -= damage
                user.current_hp += damage
            else:
                damage = formula.simple_lifeleech(user, target)
                target.current_hp -= damage
                user.current_hp += damage
            return {
                "success": bool(damage),
            }

        return {"success": False}
