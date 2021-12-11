from __future__ import annotations
import logging

from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import intentions
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from typing import Optional, Any, Callable, Generator, TYPE_CHECKING
from math import floor

if TYPE_CHECKING:
    #from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class QuantityPriceMenu(Menu[None]):
    """Menu used to select quantities."""

    def startup(
        self,
        *items: Any,
        quantity: int = 1,
        max_quantity: Optional[int] = None,
        callback: Optional[Callable[[int], None]] = None,
        shrink_to_items: bool = False,
        price: int = 1,
        buyer: Optional[NPC] = None,
        **kwargs: Any,
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
        super().startup()
        self.quantity = quantity
        self.price    = price
        buyer_money = buyer.game_variables["money"]
        self.max_quantity = min(max_quantity, floor(buyer_money / price))
        if self.quantity > self.max_quantity:
            self.quantity = self.max_quantity
        assert callback
        self.callback = callback
        self.shrink_to_items = shrink_to_items
        self.buyer    = buyer

    def on_open(self) -> None:
        logger.error(f"on_open - ")
        self.menu_items.arrange_menu_items()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:

        if event.pressed:
            if event.button in (buttons.B, buttons.BACK, intentions.MENU_CANCEL):
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
        label_format = "$ {:>{count_len}}".format

        price = (
          self.price if self.quantity == 0 
          else self.quantity * self.price
        )
        formatted_name = label_format(price, count_len=count_len)
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)
        label_format = "You have: ${:>{count_len}}".format

        if self.buyer and self.buyer.game_variables and "money" in self.buyer.game_variables:
            formatted_name = label_format(self.buyer.game_variables["money"], count_len=count_len)
        else:
            formatted_name = ""
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)
