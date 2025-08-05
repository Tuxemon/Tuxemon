# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.monster import Monster
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
@dataclass
class DieEffect(CoreEffect):
    """
    This effect applies one random status from a list to the target monster.

    Typically used by held items like "Die", which grant a random condition
    (e.g. Enraged or Sniping) when combat begins.

    Parameters:
        statuses: A colon-separated string of status slugs
            (e.g. "enraged:sniping").
    """

    name = "die"
    statuses: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        combat = item.get_combat_state()
        if combat._turn == 1:
            statuses = self.statuses.split(":")
            status_slug = random.choice(statuses)
            status = Status.create(status_slug, target)
            target.status.apply_status(session, status, target)
            combat.update_icons_for_monsters()
        return ItemEffectResult(name=item.name, success=True)
