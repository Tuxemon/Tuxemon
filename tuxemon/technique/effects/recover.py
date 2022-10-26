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


class RecoverEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class RecoverEffectParameters(NamedTuple):
    pass


class RecoverEffect(TechEffect[RecoverEffectParameters]):
    """
    This effect has a chance to apply the recovering status effect.
    """

    name = "recover"
    param_class = RecoverEffectParameters

    def apply(self, user: Monster, target: Monster) -> RecoverEffectResult:
        if self.user is None:
            already_applied = check_status(user, "status_recover")
        else:
            already_applied = check_status(self.user, "status_recover")
        success = not already_applied and self.move.potency >= random.random()
        if success:
            tech = Technique("status_recover", link=user)
            user.apply_status(tech)
            return {"status": tech}

        if already_applied:
            # avoids Nonetype situation and reset the user
            if self.user is None:
                heal = formula.simple_recover(self.move, user)
                user.current_hp += heal
            else:
                heal = formula.simple_recover(self.move, self.user)
                self.user.current_hp += heal

            return {
                "damage": heal,
                "should_tackle": False,
                "success": bool(heal),
            }

        return {"success": False}
