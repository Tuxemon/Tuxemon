# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from typing import ClassVar, Optional

from tuxemon.item.item import INFINITE_ITEMS
from tuxemon.locale import T
from tuxemon.menu.formatter import CurrencyFormatter, QuantityFormatter
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session

logger = logging.getLogger(__name__)

QUANTITY_INCREMENT = 1
QUANTITY_PAGE_INCREMENT = 10
MIN_QUANTITY = 1


class QuantityMenu(Menu[None]):
    """Menu used to select quantities."""

    name: ClassVar[str] = "QuantityMenu"

    def __init__(
        self,
        callback: Callable[[int], None],
        quantity: int = 1,
        max_quantity: Optional[int] = None,
        shrink_to_items: bool = False,
        price: int = 0,
        cost: int = 0,
        currency_formatter: Optional[CurrencyFormatter] = None,
        quantity_formatter: Optional[QuantityFormatter] = None,
    ) -> None:
        """
        Initialize the quantity menu.

        Parameters:
            quantity: Default selected quantity.
            max_quantity: Maximum selectable quantity.
            callback: Function to be called when dialog is confirmed. The
                quantity will be sent as only argument.
            shrink_to_items: Whether to fit the border to contents.
            currency_formatter: An optional formatter for currency display.
            quantity_formatter: An optional formatter for quantity display.
        """
        super().__init__()
        self.quantity = quantity
        self.price = price
        self.cost = cost
        self.max_quantity = (
            max_quantity if max_quantity != INFINITE_ITEMS else None
        )
        self.callback = callback
        self.shrink_to_items = shrink_to_items
        self.currency_formatter = currency_formatter or CurrencyFormatter()
        self.quantity_formatter = quantity_formatter or QuantityFormatter()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.pressed:
            if event.button in (
                buttons.B,
                buttons.BACK,
                intentions.MENU_CANCEL,
            ):
                self.close()
                self.callback(0)
                return None
            elif event.button == buttons.A:
                self.menu_select_sound.play()
                self.close()
                self.callback(self.quantity)
                return None
            else:
                self._update_quantity(event.button)

            self._clamp_quantity()
            self.reload_items()

        return None

    def _update_quantity(self, button: int) -> None:
        if button == buttons.UP:
            self.quantity += QUANTITY_INCREMENT
        elif button == buttons.DOWN:
            self.quantity -= QUANTITY_INCREMENT
        elif button == buttons.RIGHT:
            self.quantity += QUANTITY_PAGE_INCREMENT
        elif button == buttons.LEFT:
            self.quantity -= QUANTITY_PAGE_INCREMENT

    def _clamp_quantity(self) -> None:
        if self.max_quantity is None:
            return
        self.quantity = max(
            MIN_QUANTITY, min(self.quantity, self.max_quantity)
        )

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        label = self.quantity_formatter.format(self.quantity)
        image = self.shadow_text(label)
        yield MenuItem(image, label, None, None)

    def show_money(self) -> Generator[MenuItem[None], None, None]:
        money_manager = local_session.player.money_controller.money_manager
        formatted_money = self.currency_formatter.format(
            money_manager.get_money()
        )
        label = f"{T.translate('wallet')}: {formatted_money}"
        image_money = self.shadow_text(label)
        yield MenuItem(image_money, label, None, None)

    def calculate_total(self, value: int) -> int:
        return value if self.quantity == 0 else self.quantity * value


class QuantityAndPriceMenu(QuantityMenu):
    """Menu used to select quantities, and also shows the price of items."""

    name: ClassVar[str] = "QuantityAndPriceMenu"

    def on_open(self) -> None:
        # Do this to force the menu to resize when first opened, as currently
        # it's way too big initially and then resizes after you change quantity.
        self.menu_items.arrange_menu_items()

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        # Show the money in buying menu by using the method from the parent class:
        yield from self.show_money()

        # Show the quantity by using the method from the parent class:
        yield from super().initialize_items()

        price = self.calculate_total(self.price)
        label = self.currency_formatter.format(price)
        if price == 0:
            label = T.translate("shop_buy_free")
        image = self.shadow_text(label)
        yield MenuItem(image, label, None, None)


class QuantityAndCostMenu(QuantityMenu):
    """Menu used to select quantities, and also shows the cost of items."""

    name: ClassVar[str] = "QuantityAndCostMenu"

    def on_open(self) -> None:
        # Do this to force the menu to resize when first opened, as currently
        # it's way too big initially and then resizes after you change quantity.
        self.menu_items.arrange_menu_items()

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        # Show the money in selling menu by using the method from the parent class:
        yield from self.show_money()

        # Show the quantity by using the method from the parent class:
        yield from super().initialize_items()

        cost = self.calculate_total(self.cost)
        label = self.currency_formatter.format(cost)
        image = self.shadow_text(label)
        yield MenuItem(image, label, None, None)
