# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Callable, Generator, Optional

from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session

logger = logging.getLogger(__name__)


class QuantityMenu(Menu[None]):
    """Menu used to select quantities."""

    def __init__(
        self,
        callback: Callable[[int], None],
        quantity: int = 1,
        max_quantity: Optional[int] = None,
        shrink_to_items: bool = False,
        price: int = 0,
        cost: int = 0,
    ) -> None:
        """
        Initialize the quantity menu.

        Parameters:
            quantity: Default selected quantity.
            max_quantity: Maximum selectable quantity.
            callback: Function to be called when dialog is confirmed. The
                quantity will be sent as only argument.
            shrink_to_items: Whether to fit the border to contents.

        """
        super().__init__()
        self.quantity = quantity
        self.price = price
        self.cost = cost
        self.max_quantity = max_quantity
        self.callback = callback
        self.shrink_to_items = shrink_to_items

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

            elif event.button == buttons.UP:
                self.quantity += 1

            elif event.button == buttons.DOWN:
                self.quantity -= 1

            elif event.button == buttons.RIGHT:
                self.quantity += 10

            elif event.button == buttons.LEFT:
                self.quantity -= 10

            if self.quantity < 0:
                self.quantity = 0
            elif (
                self.max_quantity is not None
                and self.quantity > self.max_quantity
            ):
                self.quantity = self.max_quantity

            self.reload_items()

        return None

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        # TODO: move this and other format strings to a locale or config file
        label_format = "x {:>{count_len}}".format
        count_len = 3

        formatted_name = label_format(self.quantity, count_len=count_len)
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)

    def show_money(self) -> str:
        # Show the money in the buying/selling menu
        count_len = 3
        label_format_money = "Money {:>{count_len}}".format
        money = str(local_session.player.money["player"])

        formatted_name_money = label_format_money(money, count_len=count_len)
        image_money = self.shadow_text(
            formatted_name_money, bg=(128, 128, 128)
        )
        yield MenuItem(image_money, formatted_name_money, None, None)


class QuantityAndPriceMenu(QuantityMenu):
    """Menu used to select quantities, and also shows the price of items."""

    def on_open(self) -> None:
        # Do this to force the menu to resize when first opened, as currently
        # it's way too big initially and then resizes after you change quantity.
        self.menu_items.arrange_menu_items()

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        # Show the money in buying menu by using the method from the parent class:
        yield from self.show_money()

        # Show the quantity by using the method from the parent class:
        yield from super().initialize_items()

        # Now, show the price:
        label_format = "$ {:>{count_len}}".format
        count_len = 3

        price = (
            self.price if self.quantity == 0 else self.quantity * self.price
        )
        if int(price) == 0:
            price = T.translate("shop_buy_free")

        formatted_name = label_format(price, count_len=count_len)
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)


class QuantityAndCostMenu(QuantityMenu):
    """Menu used to select quantities, and also shows the cost of items."""

    def on_open(self) -> None:
        # Do this to force the menu to resize when first opened, as currently
        # it's way too big initially and then resizes after you change quantity.
        self.menu_items.arrange_menu_items()

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        # Show the money in selling menu by using the method from the parent class:
        yield from self.show_money()

        # Show the quantity by using the method from the parent class:
        yield from super().initialize_items()

        # Now, show the cost:
        label_format = "$ {:>{count_len}}".format
        count_len = 3

        cost = self.cost if self.quantity == 0 else self.quantity * self.cost
        if int(cost) == 0:
            cost = T.translate("shop_buy_free")

        formatted_name = label_format(cost, count_len=count_len)
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)
