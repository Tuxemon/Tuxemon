# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
from tuxemon.menu.menu import PygameMenuState
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
        if "bank_account" not in self.player.money:
            self.player.money["bank_account"] = 0
        bank_account = self.player.money["bank_account"]
        wallet_player = self.player.money["player"]

        _wallet = f"{T.translate('wallet')}: {wallet_player}"
        menu.add.label(
            title=_wallet,
            label_id="wallet",
            font_size=self.font_size_small,
        )
        _bank = f"{T.translate('bank')}: {bank_account}"
        menu.add.label(
            title=_bank,
            label_id="bank",
            font_size=self.font_size_small,
        )

        for key, value in self.player.money.items():
            if key.startswith("bill_") and value > 0:
                _cathedral = f"{T.translate(key)}: {value}"
                menu.add.label(
                    title=_cathedral,
                    label_id=key,
                    font_size=self.font_size_small,
                )

        elements: list[int] = [1, 10, 50, 100, 500, 1000]

        def choice(op: str, _from: str, _to: str) -> None:
            var_menu = []
            for ele in elements:
                _ele = str(ele)
                if op == "deposit" and ele <= wallet_player:
                    _param = (_ele, _ele, partial(method, ele, _from, _to))
                    var_menu.append(_param)
                if op == "withdraw" and ele <= bank_account:
                    _param = (_ele, _ele, partial(method, ele, _from, _to))
                    var_menu.append(_param)
                if op == "pay" and ele <= wallet_player:
                    _param = (_ele, _ele, partial(pay, ele, _from, _to))
                    var_menu.append(_param)
                if op == "e_pay" and ele <= bank_account:
                    _param = (_ele, _ele, partial(pay, ele, _from, _to))
                    var_menu.append(_param)
            if var_menu:
                if op == "pay" or op == "e_pay":
                    self.client.pop_state()
                open_choice_dialog(local_session, (var_menu), True)
            else:
                params = {"operation": T.translate(op)}
                msg = T.format("no_money_operation", params)
                open_dialog(local_session, [msg])

        def bill(op: str, _from: str) -> None:
            var_menu = []
            for key, value in self.player.money.items():
                _key = T.translate(key)
                if key.startswith("bill_") and value > 0:
                    _param = (_key, _key, partial(choice, op, _from, key))
                    var_menu.append(_param)
            if var_menu:
                open_choice_dialog(local_session, (var_menu), True)
            else:
                params = {"operation": T.translate(op)}
                msg = T.format("no_money_operation", params)
                open_dialog(local_session, [msg])

        def method(amount: int, _from: str, _to: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money[_from] -= amount
            self.player.money[_to] += amount

        def pay(amount: int, _from: str, _to: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money[_from] -= amount
            self.player.money[_to] -= amount

        if wallet_player > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                title=T.translate("deposit").upper(),
                action=partial(choice, "deposit", "player", "bank_account"),
                button_id="deposit",
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
        if bank_account > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                title=T.translate("withdraw").upper(),
                action=partial(choice, "withdraw", "bank_account", "player"),
                button_id="withdraw",
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )

        _payment = False
        _e_payment = False
        for key, value in self.player.money.items():
            if key.startswith("bill_"):
                if value > 0 and wallet_player > 0:
                    _payment = True
                if value > 0 and bank_account > 0:
                    _e_payment = True

        if _payment:
            menu.add.vertical_margin(25)
            _pay = T.translate("pay").upper()
            menu.add.button(
                title=_pay,
                action=partial(bill, "pay", "player"),
                button_id=_pay,
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )

        if _e_payment:
            menu.add.vertical_margin(25)
            _pay = T.translate("e_pay").upper()
            menu.add.button(
                title=_pay,
                action=partial(bill, "e_pay", "bank_account"),
                button_id=_pay,
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
        menu.set_title(T.translate("app_banking")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                prepare.BG_PHONE_BANKING
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

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
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
