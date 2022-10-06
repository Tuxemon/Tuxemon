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

import operator
import random
from typing import NamedTuple

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult


class StatChangeEffectResult(TechEffectResult):
    pass


class StatChangeEffectParameters(NamedTuple):
    pass


class StatChangeEffect(TechEffect[StatChangeEffectParameters]):
    """
    Change combat stats.

    JSON SYNTAX:
        value: The number to change the stat by, default is add, use
            negative to subtract.
        dividing: Set this to True to divide instead of adding or
            subtracting the value.
        overridetofull: In most cases you wont need this. If ``True`` it
            will set the stat to its original value rather than the
            specified value, but due to the way the
            game is coded, it currently only works on hp.

    """

    name = "statchange"
    param_class = StatChangeEffectParameters

    def apply(self, user: Monster, target: Monster) -> StatChangeEffectResult:
        statsmaster = [
            self.move.statspeed,
            self.move.stathp,
            self.move.statarmour,
            self.move.statmelee,
            self.move.statranged,
            self.move.statdodge,
        ]
        statslugs = [
            "speed",
            "current_hp",
            "armour",
            "melee",
            "ranged",
            "dodge",
        ]
        newstatvalue = 0
        for stat, slugdata in zip(statsmaster, statslugs):
            if not stat:
                continue
            value = stat.value
            max_deviation = stat.max_deviation
            operation = stat.operation
            override = stat.overridetofull
            basestatvalue = getattr(target, slugdata)
            if max_deviation:
                value = random.randint(
                    value - max_deviation,
                    value + max_deviation,
                )

            if value > 0 and override is not True:
                ops_dict = {
                    "+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.floordiv,
                }
                newstatvalue = ops_dict[operation](basestatvalue, value)
            if slugdata == "current_hp":
                if override:
                    target.current_hp = target.hp
            if newstatvalue <= 0:
                newstatvalue = 1
            setattr(target, slugdata, newstatvalue)
        return {"success": bool(newstatvalue)}
