# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class LearnTmEffect(CoreEffect):
    """
    Teaches a specific technique (TM) to the target monster.

    This effect should be used when an item allows a monster to learn a fixed
    technique, such as with a TM or scroll.

    Parameters:
        technique: Slug of the technique to be taught (e.g., "ram", "ice_beam").
    """

    name = "learn_tm"
    technique: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if target.moves.has_move(self.technique):
            return ItemEffectResult(name=item.name)
        tech = Technique.create(self.technique)
        learned = target.moves.learn(target, tech)
        if not learned:
            return ItemEffectResult(name=item.name)
        return ItemEffectResult(name=item.name, success=True)
