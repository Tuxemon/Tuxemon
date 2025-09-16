# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
class BivouacEffect(CoreEffect):
    """
    Fully restores a monster's health and clears any status conditions,
    simulating rest at a formal healing center.
    """

    name = "bivouac"

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        session.client.event_engine.execute_action("set_monster_health")
        session.client.event_engine.execute_action("set_monster_status")
        return ItemEffectResult(name=item.name, success=True)
