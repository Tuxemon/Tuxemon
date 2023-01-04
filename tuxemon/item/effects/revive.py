# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class ReviveEffectResult(ItemEffectResult):
    pass


@dataclass
class ReviveEffect(ItemEffect):
    """
    Revives the target tuxemon, and sets HP to 1.
    """

    name = "revive"
    hp: int

    def apply(self, target: Monster) -> ReviveEffectResult:
        target.status = []
        target.current_hp = self.hp

        return {"success": True}
