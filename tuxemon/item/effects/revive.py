# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
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

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ReviveEffectResult:
        assert target
        target.status = []
        target.current_hp = self.hp

        return {"success": True, "num_shakes": 0, "extra": None}
