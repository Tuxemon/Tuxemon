import logging

import pygame
import pygame_gui

from tuxemon.locale import T
from pygame_gui.elements import UIPanel, UIButton
from pygame_gui import UIManager
from pygame.rect import Rect
from pygame.event import Event

logger = logging.getLogger(__name__)


class SimpleMenu(UIPanel):
    """
    A simple menu class that takes a dictionary of localization keys and callbacks.
    Automatically creates a menu with buttons using the translated text and will use the callbacks when the
    appropriate button is chosen by the player.
    """

    def __init__(self, manager: UIManager, container, pos: tuple, ui_id: str, menu_items: dict):
        # gotta do something a little more sophisticated than this in future
        button_height = 20
        height = len(menu_items) * button_height
        width = 200  # way more sophisticated...

        super().__init__(relative_rect=Rect(pos, (height, width)),
                         starting_layer_height=1,
                         manager=manager,
                         container=container,
                         object_id=ui_id)

        self.buttons = []
        x = y = 0
        for key, callback in menu_items:
            self.buttons.append(UIButton(
                relative_rect=Rect((x, y), (width, button_height)),
                text=T.translate(key),
                manager=manager,
                container=self,
                starting_height=button_height,
                parent_element=self,
                object_id=key
            ))

        self.callbacks = menu_items
        self.buttons[0].select()

    def process_event(self, event: Event):
        if event.type != pygame.USEREVENT:
            return
        handled = super().process_event(event)
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            for button in self.buttons:
                if button.check_pressed():
                    self.callbacks[button.object_ids[-1]]()
                    handled = True
                    break
        if event.user_type == pygame.KEYDOWN:

        return handled
