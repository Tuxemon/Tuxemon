# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER

from tuxemon.locale.locale import T
from tuxemon.menu.formatter import CurrencyFormatter, QuantityFormatter
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BG_MISSIONS

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class QuantityPickerState(PygameMenuState):
    """Compact, centered, supports +/- and held-button repeat."""

    name: ClassVar[str] = "QuantityPickerState"

    def __init__(
        self,
        client: BaseClient,
        *,
        min_value: int = 1,
        max_value: int | None = None,
        start_value: int = 1,
        step: int = 1,
        callback: Callable[[int], None],
        title: str | None = None,
        price: int | None = None,
        cost: int | None = None,
        wallet_money: int | None = None,
        escape_key_exits: bool | None = None,
        currency_formatter: CurrencyFormatter | None = None,
        quantity_formatter: QuantityFormatter | None = None,
        **kwargs: Any,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.callback = callback
        self.current_value = start_value
        self.title = title or T.translate("select_number")

        self.price = price
        self.cost = cost
        self.wallet_money = wallet_money

        self.currency = currency_formatter or CurrencyFormatter()
        self.quantity = quantity_formatter or QuantityFormatter()

        width, height = client.context.resolution
        width = int(0.45 * width)
        height = int(0.45 * height)
        super().__init__(client=client, width=width, height=height, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        if escape_key_exits is not None:
            self.escape_key_exits = escape_key_exits

        self._build_menu()
        self.reset_theme()

    def _build_menu(self) -> None:
        self.menu.clear()
        self.menu.set_title(self.title).center_content()

        # Wallet display (optional)
        if self.wallet_money is not None:
            self.menu.add.label(
                f"{T.translate('wallet')}: {self.currency.format(self.wallet_money)}",
                font_size=self.font_type.small,
                align=ALIGN_CENTER,
            )

        # Instructions
        self.menu.add.label(
            T.translate("number_picker_instructions"),
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
        )

        # Row with - [value] +
        row = self.menu.add.frame_h(300, 70)
        row._relax = True

        minus_btn = self.menu.add.button(
            "-",
            lambda: self._decrement(),
            font_size=self.font_type.big,
        )
        row.pack(minus_btn, align=ALIGN_CENTER)

        self.value_label: Any = self.menu.add.label(
            self.quantity.format(self.current_value),
            font_size=self.font_type.big,
        )
        row.pack(self.value_label, align=ALIGN_CENTER)

        plus_btn = self.menu.add.button(
            "+",
            lambda: self._increment(),
            font_size=self.font_type.big,
        )
        row.pack(plus_btn, align=ALIGN_CENTER)

        # Price/cost display (optional)
        if self.price is not None or self.cost is not None:
            self.total_label: Any = self.menu.add.label(
                self._compute_total_label(),
                font_size=self.font_type.small,
                align=ALIGN_CENTER,
            )

    def _compute_total_label(self) -> str:
        # Price mode
        if self.price is not None:
            total = self.current_value * self.price

            if self.wallet_money is not None and total > self.wallet_money:
                return T.translate("shop_buy_too_expensive")

            if total == 0:
                return T.translate("shop_buy_free")

            return self.currency.format(total)

        # Cost mode
        if self.cost is not None:
            return self.currency.format(self.current_value * self.cost)

        return ""

    def _update_labels(self) -> None:
        self.value_label.set_title(self.quantity.format(self.current_value))
        if hasattr(self, "total_label"):
            self.total_label.set_title(self._compute_total_label())

    def _increment(self) -> None:
        new_value = self.current_value + self.step
        if self.max_value is None or new_value <= self.max_value:
            self.current_value = new_value
            self._update_labels()

    def _decrement(self) -> None:
        new_value = self.current_value - self.step
        if new_value >= self.min_value:
            self.current_value = new_value
            self._update_labels()

    def _confirm(self) -> None:
        self.callback(self.current_value)
        self.client.pop_state()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # RIGHT = increment
        if event.button == buttons.RIGHT and self.valid_press(event):
            self._increment()
            return None

        # LEFT = decrement
        if event.button == buttons.LEFT and self.valid_press(event):
            self._decrement()
            return None

        # A = confirm
        if event.button == buttons.A and event.pressed:
            self._confirm()
            return None

        # B = cancel
        if event.button == buttons.B and event.pressed:
            self.client.pop_state()
            return None

        return event
