# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class RestoreEffectResult(ItemEffectResult):
    pass


@dataclass
class RestoreEffect(ItemEffect):
    """
    Remove any condition.

    """

    name = "restore"

    def apply(self, target: Monster) -> RestoreEffectResult:
        target.status.clear()
        return {"success": True}
