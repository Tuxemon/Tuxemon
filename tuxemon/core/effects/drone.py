# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.prepare import KENNEL

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class DroneEffect(CoreEffect):
    """
    Swaps a monster from the player's party with one from the specified monster
    box (KENNEL). When used, the player selects a party monster to be swapped
    with a monster from the box. If no monsters are available in the box, the
    effect fails.
    """

    name = "drone"

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:

        def on_party_monster_selected(monster: Monster) -> None:
            session.client.push_state(
                "MonsterTakeState",
                box_name=KENNEL,
                character=session.player,
                swap_target=monster,
            )

        size = session.player.monster_boxes.get_box_size(KENNEL, "monster")
        if size == 0:
            return ItemEffectResult(name=item.name)

        session.client.push_state(
            "MonsterDropOff",
            box_name=KENNEL,
            character=session.player,
            on_selection=on_party_monster_selected,
        )
        return ItemEffectResult(name=item.name, success=True)
