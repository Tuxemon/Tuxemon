# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


class LearnEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnEffect(ItemEffect):
    """This effect teaches the target the technique in the parameters."""

    name = "learn"
    technique: str

    def apply(self, target: Monster) -> LearnEffectResult:
        tech = Technique()
        tech.load(self.technique)
        target.learn(tech)

        return {"success": True}
