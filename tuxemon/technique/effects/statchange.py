# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import operator
import random
from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class StatChangeEffectResult(TechEffectResult):
    pass


@dataclass
class StatChangeEffect(TechEffect):
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
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> StatChangeEffectResult:
        statsmaster = [
            tech.statspeed,
            tech.stathp,
            tech.statarmour,
            tech.statmelee,
            tech.statranged,
            tech.statdodge,
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
