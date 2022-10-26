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


class PoisonEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class PoisonEffectParameters(NamedTuple):
    pass


class PoisonEffect(TechEffect[PoisonEffectParameters]):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"
    param_class = PoisonEffectParameters

    def apply(self, user: Monster, target: Monster) -> PoisonEffectResult:
        already_applied = check_status(target, "status_poison")
        success = not already_applied and self.move.potency >= random.random()
        if success:
            tech = Technique("status_poison", carrier=target)
            target.apply_status(tech)
            # exception: applies status to the user
            if self.move.slug == "fester":
                user.apply_status(tech)
            return {"status": tech}

        if already_applied:
            damage = formula.simple_poison(self.move, target)
            target.current_hp -= damage

            return {
                "damage": damage,
                "should_tackle": bool(damage),
                "success": bool(damage),
            }

        return {"success": False}
