from __future__ import division, print_function
from __future__ import unicode_literals

import logging

import pygame

from tuxemon.core.components.menu.interface import MenuItem
from tuxemon.core.components.menu.menu import Menu

logger = logging.getLogger(__name__)


class QuantityMenu(Menu):
    def startup(self, *items, **kwargs):
        super(QuantityMenu, self).startup()
        self.quantity = kwargs.get("quantity", 1)
        self.max_quantity = kwargs.get("max_quantity")
        self.callback = kwargs.get("callback")
        self.shrink_to_items = kwargs.get("shrink_to_items", False)

    def process_event(self, event):
        """ Process pygame input events

        The menu cursor is handled here, as well as the ESC and ENTER keys.

        :param event: pygame.Event
        :returns: None
        """
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.close()
                self.callback(0)
                return

            elif event.key == pygame.K_RETURN:
                self.menu_select_sound.play()
                self.close()
                self.callback(self.quantity)
                return

            elif event.key == pygame.K_UP:
                self.quantity += 1

            elif event.key == pygame.K_DOWN:
                self.quantity -= 1

            elif event.key == pygame.K_RIGHT:
                self.quantity += 10

            elif event.key == pygame.K_LEFT:
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

