#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#

from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon import formula
from tuxemon.combat import check_status
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class LifeLeechEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class LifeLeechEffectParameters(NamedTuple):
    pass


class LifeLeechEffect(TechEffect[LifeLeechEffectParameters]):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "lifeleech"
    param_class = LifeLeechEffectParameters

    def apply(self, user: Monster, target: Monster) -> LifeLeechEffectResult:
        already_applied = check_status(target, "status_lifeleech")
        success = not already_applied and self.move.potency >= random.random()
        if success:
            tech = Technique("status_lifeleech", carrier=target, link=user)
            target.apply_status(tech)
            # exception: applies status to the user
            if self.move.slug == "blood_bond":
                tech = Technique("status_lifeleech", carrier=user, link=target)
                user.apply_status(tech)
            return {"status": tech}

        if already_applied:
            # avoids Nonetype situation and reset the user
            if self.user is None:
                damage = formula.simple_lifeleech(self.move, user, target)
                target.current_hp -= damage
                user.current_hp += damage
            else:
                damage = formula.simple_lifeleech(self.move, self.user, target)
                target.current_hp -= damage
                self.user.current_hp += damage

            return {
                "damage": damage,
                "should_tackle": bool(damage),
                "success": bool(damage),
            }

        return {"success": False}
