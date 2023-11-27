# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare, tools
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog, open_dialog

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneBanking(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        if "bank_account" not in self.player.money:
            self.player.money["bank_account"] = 0
        bank = self.player.money["bank_account"]
        money = self.player.money["player"]
        menu.add.label(
            title=T.translate("wallet") + ": " + str(money),
            label_id="wallet",
            font_size=round(0.015 * width),
        )
        menu.add.label(
            title=T.translate("bank") + ": " + str(bank),
            label_id="bank",
            font_size=round(0.015 * width),
        )

        elements = [
            100,
            200,
            500,
            1000,
            2000,
            5000,
            10000,
            20000,
            50000,
            100000,
        ]

        def choice_deposit() -> None:
            var_menu = []
            for ele in elements:
                if ele <= money:
                    var_menu.append(
                        (str(ele), str(ele), partial(deposit, ele))
                    )
            if var_menu:
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )
            else:
                open_dialog(
                    local_session,
                    [
                        T.format(
                            "no_money_operation",
                            {"operation": T.translate("deposit")},
                        )
                    ],
                )

        def choice_withdraw() -> None:
            var_menu = []
            for ele in elements:
                if ele <= bank:
                    var_menu.append(
                        (str(ele), str(ele), partial(withdraw, ele))
                    )
            if var_menu:
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )
            else:
                open_dialog(
                    local_session,
                    [
                        T.format(
                            "no_money_operation",
                            {"operation": T.translate("withdraw")},
                        )
                    ],
                )

        def deposit(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money["player"] -= amount
            self.player.money["bank_account"] += amount

        def withdraw(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money["player"] += amount
            self.player.money["bank_account"] -= amount

        menu.add.vertical_margin(100)
        # deposit
        menu.add.button(
            title=T.translate("deposit").upper(),
            action=choice_deposit,
            button_id="deposit",
            font_size=round(0.015 * width),
            selection_effect=HighlightSelection(),
        )
        menu.add.vertical_margin(100)
        # withdraw
        menu.add.button(
            title=T.translate("withdraw").upper(),
            action=choice_withdraw,
            button_id="withdraw",
            font_size=round(0.015 * width),
            selection_effect=HighlightSelection(),
        )
        # menu
        menu.set_title(T.translate("app_banking")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True
        theme.title_font_size = round(0.025 * width)

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
