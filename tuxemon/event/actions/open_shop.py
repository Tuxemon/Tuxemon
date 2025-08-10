# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.npc import NPC
from tuxemon.session import Session
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

logger = logging.getLogger(__name__)


@final
@dataclass
class OpenShopAction(EventAction):
    """
    Opens a shop interface between the player and a target NPC.

    Script usage:
        open_shop <npc_slug>,<menu>

    Parameters:
        npc_slug: Either "player" or the NPC slug identifier (e.g. "npc_maple").
        menu: Type of shop interaction to open. Must be one of:
            - "buy_item"
            - "sell_item"
            - "both_item"
            - "buy_monster"
            - "sell_monster"
            - "both_monster"

    Notes:
        - The target NPC must have an economy assigned.
        - If menu is "both_*", a choice dialog is shown for selection.
    """

    name = "open_shop"
    npc_slug: str
    menu: str

    def start(self, session: Session) -> None:
        valid_menus = {
            "buy_item",
            "sell_item",
            "both_item",
            "buy_monster",
            "sell_monster",
            "both_monster",
        }

        if self.menu not in valid_menus:
            raise ValueError(
                f"Invalid menu: '{self.menu}'. Must be one of: {', '.join(sorted(valid_menus))}"
            )

        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"NPC '{self.npc_slug}' not found.")
            return

        if character.economy is None:
            raise ValueError(
                f"NPC '{character.slug}' has no assigned economy."
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

        def wrap_choice_dialog(options: MenuOptions) -> None:
            open_choice_dialog(
                client=session.client,
                menu=options,
                escape_key_exits=True,
            )

        # Define menu option groups
        items = MenuOptions(
            [
                ChoiceOption(
                    key="buy",
                    display_text=T.translate("buy"),
                    action=partial(
                        push_state,
                        "ShopItemBuyMenuState",
                        session.player,
                        character,
                    ),
                ),
                ChoiceOption(
                    key="sell",
                    display_text=T.translate("sell"),
                    action=partial(
                        push_state,
                        "ShopItemSellMenuState",
                        character,
                        session.player,
                    ),
                ),
            ]
        )

        monsters = MenuOptions(
            [
                ChoiceOption(
                    key="buy",
                    display_text=T.translate("buy"),
                    action=partial(
                        push_state,
                        "ShopMonsterBuyMenuState",
                        session.player,
                        character,
                    ),
                ),
                ChoiceOption(
                    key="sell",
                    display_text=T.translate("sell"),
                    action=partial(
                        push_state,
                        "ShopMonsterSellMenuState",
                        character,
                        session.player,
                    ),
                ),
            ]
        )

        # Dispatch based on menu mode
        if self.menu == "both_item":
            wrap_choice_dialog(items)
        elif self.menu == "both_monster":
            wrap_choice_dialog(monsters)
        elif self.menu == "buy_item":
            push_state("ShopItemBuyMenuState", session.player, character)
        elif self.menu == "sell_item":
            push_state("ShopItemSellMenuState", character, session.player)
        elif self.menu == "buy_monster":
            push_state("ShopMonsterBuyMenuState", session.player, character)
        elif self.menu == "sell_monster":
            push_state("ShopMonsterSellMenuState", character, session.player)
