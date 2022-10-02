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

from typing import NamedTuple

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult


class PoisonEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool


class PoisonEffectParameters(NamedTuple):
    pass


class PoisonEffect(TechEffect[PoisonEffectParameters]):
    """
    Poison
    """

    name = "poison"
    param_class = PoisonEffectParameters

    def apply(self, user: Monster, target: Monster) -> PoisonEffectResult:
        damage = formula.simple_poison(self.move, target)
        target.current_hp -= damage
        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
