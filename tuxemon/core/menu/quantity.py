import logging

from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import Menu
from tuxemon.core.platform.const import buttons, intentions

logger = logging.getLogger(__name__)


class QuantityMenu(Menu):
    def startup(self, *items, **kwargs):
        super().startup()
        self.quantity = kwargs.get("quantity", 1)
        self.max_quantity = kwargs.get("max_quantity")
        self.callback = kwargs.get("callback")
        self.shrink_to_items = kwargs.get("shrink_to_items", False)

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        if event.pressed:
            if event.button in (buttons.B, buttons.BACK, intentions.MENU_CANCEL):
                self.close()
                self.callback(0)
                return

            elif event.button == buttons.A:
                self.menu_select_sound.play()
                self.close()
                self.callback(self.quantity)
                return

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
            elif self.max_quantity is not None and self.quantity > self.max_quantity:
                self.quantity = self.max_quantity

            self.reload_items()

    def initialize_items(self):
        # TODO: move this and other format strings to a locale or config file
        label_format = "x {:>{count_len}}".format
        count_len = 3

        formatted_name = label_format(self.quantity, count_len=count_len)
        image = self.shadow_text(formatted_name, bg=(128, 128, 128))
        yield MenuItem(image, formatted_name, None, None)
