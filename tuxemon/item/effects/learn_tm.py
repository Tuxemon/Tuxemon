from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


class LearnTmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnTmEffect(ItemEffect):
    """This effect teaches the target the technique in the parameters."""

    name = "learn_tm"
    technique: str

    def apply(self, target: Monster) -> LearnTmEffectResult:
        tech = Technique()
        tech.load(self.technique)
        target.learn(tech)

        return {"success": True}
