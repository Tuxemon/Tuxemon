# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
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
        money_manager = self.player.money_controller.money_manager
        bank_account = money_manager.get_bank_balance()
        wallet_player = money_manager.get_money()

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

        for key, entry in money_manager.bills.items():
            if entry.amount > 0:
                _cathedral = f"{T.translate(key)}: {entry.amount}"
                menu.add.label(
                    title=_cathedral,
                    label_id=key,
                    font_size=self.font_size_small,
                )

        elements: list[int] = [1, 10, 50, 100, 500, 1000]

        def choice(op: str) -> None:
            var_menu = []
            for ele in elements:
                _ele = str(ele)
                if op == "deposit" and ele <= wallet_player:
                    _param = (_ele, _ele, partial(deposit, ele))
                    var_menu.append(_param)
                if op == "withdraw" and ele <= bank_account:
                    _param = (_ele, _ele, partial(withdraw, ele))
                    var_menu.append(_param)
                if op == "pay" and ele <= wallet_player:
                    _param = (_ele, _ele, partial(pay, ele))
                    var_menu.append(_param)
                if op == "e_pay" and ele <= bank_account:
                    _param = (_ele, _ele, partial(e_pay, ele))
                    var_menu.append(_param)
            if var_menu:
                open_choice_dialog(local_session, (var_menu), True)
            else:
                params = {"operation": T.translate(op)}
                msg = T.format("no_money_operation", params)
                open_dialog(local_session, [msg])

        def bill_manager(op: str, bill_name: str) -> None:
            var_menu = []
            for ele in elements:
                _ele = str(ele)
                if op == "pay" and ele <= wallet_player:
                    _param = (_ele, _ele, partial(pay, ele, bill_name))
                    var_menu.append(_param)
                if op == "e_pay" and ele <= bank_account:
                    _param = (_ele, _ele, partial(e_pay, ele, bill_name))
                    var_menu.append(_param)
            if var_menu:
                self.client.pop_state()
                open_choice_dialog(local_session, (var_menu), True)
            else:
                params = {"operation": T.translate(op)}
                msg = T.format("no_money_operation", params)
                open_dialog(local_session, [msg])

        def bill(op: str) -> None:
            var_menu = []
            for key, entry in money_manager.bills.items():
                _key = T.translate(key)
                if entry.amount > 0:
                    _param = (_key, _key, partial(bill_manager, op, key))
                    var_menu.append(_param)
            if var_menu:
                open_choice_dialog(local_session, (var_menu), True)
            else:
                params = {"operation": T.translate(op)}
                msg = T.format("no_money_operation", params)
                open_dialog(local_session, [msg])

        def deposit(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            money_manager.deposit_to_bank(amount)
            money_manager.remove_money(amount)

        def withdraw(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            money_manager.withdraw_from_bank(amount)
            money_manager.add_money(amount)

        def pay(amount: int, bill_name: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            money_manager.pay_bill_with_money(bill_name, amount)

        def e_pay(amount: int, bill_name: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            money_manager.pay_bill_with_deposit(bill_name, amount)

        if wallet_player > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                title=T.translate("deposit").upper(),
                action=partial(choice, "deposit"),
                button_id="deposit",
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
        if bank_account > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                title=T.translate("withdraw").upper(),
                action=partial(choice, "withdraw"),
                button_id="withdraw",
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )

        _payment = False
        _e_payment = False
        for key, entry in money_manager.bills.items():
            if entry.amount > 0 and wallet_player > 0:
                _payment = True
            if entry.amount > 0 and bank_account > 0:
                _e_payment = True

        if _payment:
            menu.add.vertical_margin(25)
            _pay = T.translate("pay").upper()
            menu.add.button(
                title=_pay,
                action=partial(bill, "pay"),
                button_id=_pay,
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )

        if _e_payment:
            menu.add.vertical_margin(25)
            _pay = T.translate("e_pay").upper()
            menu.add.button(
                title=_pay,
                action=partial(bill, "e_pay"),
                button_id=_pay,
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
        menu.set_title(T.translate("app_banking")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE_BANKING)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.reset_theme()
