# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class OpenShopAction(EventAction):
    """
    Opens a shop interface between the player and a target NPC.

    Script usage:
        open_shop <npc_slug>,<menu>[,model]

    Parameters:
        npc_slug: Either "player" or the NPC slug identifier (e.g. "npc_maple").
        menu: Type of shop interaction to open. Must be one of:
            - "buy_item"
            - "sell_item"
            - "both_item"
            - "buy_monster"
            - "sell_monster"
            - "both_monster"
            - "train_monster"
            - "heal_monster"
        model (optional): A configuration profile name used to load custom shop behavior.

    Notes:
        - The target NPC must have an economy assigned.
        - If menu is "both_*", a choice dialog is shown for selection.
    """

    name = "open_shop"
    npc_slug: str
    menu: str
    model: str | None = None

    def start(self, session: Session) -> None:
        valid_menus = {
            "buy_item",
            "sell_item",
            "both_item",
            "buy_monster",
            "sell_monster",
            "both_monster",
            "train_monster",
            "heal_monster",
        }

        if self.menu not in valid_menus:
            raise ValueError(
                f"Invalid menu: '{self.menu}'. Must be one of: "
                f"{', '.join(sorted(valid_menus))}"
            )

        character = session.client.get_npc(self.npc_slug)
        if character is None:
            logger.error(f"NPC '{self.npc_slug}' not found.")
            self.stop()
            return

        # Only item/monster shops require an economy
        if character.economy is None and self.menu not in {
            "train_monster",
            "heal_monster",
        }:
            raise ValueError(
                f"NPC '{character.slug}' has no assigned economy. "
                "Use the 'set_economy' EventAction first."
            )

        economy = character.economy

        def push_state(state_name: str, buyer: NPC, seller: NPC) -> None:
            session.client.push_state(
                state_name,
                buyer=buyer,
                seller=seller,
                economy=economy,
            )

        if self.menu == "both_item":
            session.client.push_state(
                "ShopChoiceState",
                session=session,
                npc=character,
                mode="item",
            )
            self.stop()
            return

        if self.menu == "both_monster":
            session.client.push_state(
                "ShopChoiceState",
                session=session,
                npc=character,
                mode="monster",
            )
            self.stop()
            return

        if self.menu == "buy_item":
            push_state("ShopItemBuyMenuState", session.player, character)
        elif self.menu == "sell_item":
            push_state("ShopItemSellMenuState", character, session.player)
        elif self.menu == "buy_monster":
            push_state("ShopMonsterBuyMenuState", session.player, character)
        elif self.menu == "sell_monster":
            push_state("ShopMonsterSellMenuState", character, session.player)
        elif self.menu == "train_monster":
            session.client.push_state(
                "ShopTrainingMenuState",
                buyer=character,
                seller=session.player,
                economy=economy,
                model=self.model,
            )
        elif self.menu == "heal_monster":
            session.client.push_state(
                "ShopHealingMenuState",
                buyer=character,
                seller=session.player,
                economy=economy,
                model=self.model,
            )
