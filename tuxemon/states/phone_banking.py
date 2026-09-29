# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.locale.locale import T
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE_BANKING
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import MenuOptions, create_choice_options

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


class NuPhoneBanking(PygameMenuState):
    name: ClassVar[str] = "NuPhoneBanking"

    def _deposit(self, amount: int) -> None:
        mm = self.char.money_controller.money_manager
        mm.deposit_to_bank(amount)
        mm.remove_money(amount)
        self.client.remove_state_by_name("NuPhoneBanking")

    def _withdraw(self, amount: int) -> None:
        mm = self.char.money_controller.money_manager
        mm.withdraw_from_bank(amount)
        mm.add_money(amount)
        self.client.remove_state_by_name("NuPhoneBanking")

    def _pay(self, amount: int, bill_name: str) -> None:
        mm = self.char.money_controller.money_manager
        mm.pay_bill_with_money(bill_name, amount)
        self.client.remove_state_by_name("NuPhoneBanking")

    def _e_pay(self, amount: int, bill_name: str) -> None:
        mm = self.char.money_controller.money_manager
        mm.pay_bill_with_deposit(bill_name, amount)
        self.client.remove_state_by_name("NuPhoneBanking")

    def _open_amount_picker(
        self,
        max_value: int,
        callback: Callable[[int], None],
        title: str,
    ) -> None:
        if max_value <= 0:
            msg = T.format("no_money_operation", {"operation": title})
            open_dialog(self.client, [msg], dialog_speed="max")
            return

        self.client.push_state(
            "NumberPickerState",
            min_value=0,
            max_value=max_value,
            callback=callback,
            title=title,
            step=100,
            escape_key_exits=True,
        )

    def _select_bill(self, op: str) -> None:
        mm = self.char.money_controller.money_manager

        bills = {
            key: entry.amount
            for key, entry in mm.bills.items()
            if entry.amount > 0
        }

        if not bills:
            msg = T.format(
                "no_money_operation", {"operation": T.translate(op)}
            )
            open_dialog(self.client, [msg], dialog_speed="max")
            return

        actions = {
            key: (lambda k=key: self._select_bill_amount(op, k))
            for key in bills
        }

        options = create_choice_options(actions)
        for opt in options:
            opt.display_text = T.translate(opt.key)

        menu = MenuOptions(options)
        open_choice_dialog(self.client, menu, escape_key_exits=True)

    def _select_bill_amount(self, op: str, bill_name: str) -> None:
        mm = self.char.money_controller.money_manager

        if op == "pay":
            max_value = mm.get_money()

            def callback(amount: int) -> None:
                return self._pay(amount, bill_name)
        else:
            max_value = mm.get_bank_balance()

            def callback(amount: int) -> None:
                return self._e_pay(amount, bill_name)

        self._open_amount_picker(
            max_value=max_value,
            callback=callback,
            title=T.translate(op),
        )

    def add_menu_items(self, menu: Menu) -> None:
        mm = self.char.money_controller.money_manager
        bank_account = mm.get_bank_balance()
        wallet_player = mm.get_money()

        formatter = CurrencyFormatter()
        menu.add.label(
            f"{T.translate('wallet')}: {formatter.format(wallet_player)}",
            label_id="wallet",
            font_size=self.font_type.small,
        )
        menu.add.label(
            f"{T.translate('bank')}: {formatter.format(bank_account)}",
            label_id="bank",
            font_size=self.font_type.small,
        )

        # Bills
        for key, entry in mm.bills.items():
            if entry.amount > 0:
                menu.add.label(
                    f"{T.translate(key)}: {entry.amount}",
                    label_id=key,
                    font_size=self.font_type.small,
                )

        # Deposit
        if wallet_player > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                T.translate("deposit").upper(),
                lambda: self._open_amount_picker(
                    max_value=wallet_player,
                    callback=self._deposit,
                    title=T.translate("deposit"),
                ),
                button_id="deposit",
                font_size=self.font_type.small,
                selection_effect=HighlightSelection(),
            )

        # Withdraw
        if bank_account > 0:
            menu.add.vertical_margin(25)
            menu.add.button(
                T.translate("withdraw").upper(),
                lambda: self._open_amount_picker(
                    max_value=bank_account,
                    callback=self._withdraw,
                    title=T.translate("withdraw"),
                ),
                button_id="withdraw",
                font_size=self.font_type.small,
                selection_effect=HighlightSelection(),
            )

        # Pay bills
        has_wallet_bills = (
            any(entry.amount > 0 for entry in mm.bills.values())
            and wallet_player > 0
        )

        has_bank_bills = (
            any(entry.amount > 0 for entry in mm.bills.values())
            and bank_account > 0
        )

        if has_wallet_bills:
            menu.add.vertical_margin(25)
            menu.add.button(
                T.translate("pay").upper(),
                lambda: self._select_bill("pay"),
                button_id="pay",
                font_size=self.font_type.small,
                selection_effect=HighlightSelection(),
            )

        if has_bank_bills:
            menu.add.vertical_margin(25)
            menu.add.button(
                T.translate("e_pay").upper(),
                lambda: self._select_bill("e_pay"),
                button_id="e_pay",
                font_size=self.font_type.small,
                selection_effect=HighlightSelection(),
            )

        menu.set_title(T.translate("app_banking")).center_content()

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character
        width, height = client.context.resolution
        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE_BANKING)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
