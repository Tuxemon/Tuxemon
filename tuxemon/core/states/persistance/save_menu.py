import logging
import os
from base64 import b64decode

import pygame

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core import save
from tuxemon.core.locale import T
from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import PopUpMenu
from tuxemon.core.session import local_session
from tuxemon.core.tools import open_dialog
from tuxemon.core.ui import text

logger = logging.getLogger(__name__)


class SaveMenuState(PopUpMenu):
    number_of_slots = 3
    shrink_to_items = True

    def startup(self, *items, **kwargs):
        if 'selected_index' not in kwargs:
            kwargs['selected_index'] = save.slot_number or 0
        super().startup(*items, **kwargs)

    def initialize_items(self):
        empty_image = None
        rect = self.client.screen.get_rect()
        slot_rect = Rect(0, 0, rect.width * 0.80, rect.height // 6)
        for i in range(self.number_of_slots):
            # Check to see if a save exists for the current slot
            if os.path.exists(prepare.SAVE_PATH + str(i + 1) + ".save"):
                image = self.render_slot(slot_rect, i + 1)
                item = MenuItem(image, T.translate('menu_save'), None, None)
                self.add(item)
            else:
                if not empty_image:
                    empty_image = self.render_empty_slot(slot_rect)
                item = MenuItem(empty_image, "SAVE", None, None)
                self.add(item)

    def render_empty_slot(self, rect):
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)
        rect = rect.move(0, rect.height // 2 - 10)
        text.draw_text(slot_image, T.translate('empty_slot'), rect, font=self.font)
        return slot_image

    def render_slot(self, rect, slot_num):
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)

        # Try and load the save game and draw details about the save
        save_data = save.load(slot_num)
        if "screenshot" in save_data:
            screenshot = b64decode(save_data["screenshot"])
            size = save_data["screenshot_width"], save_data["screenshot_height"]
            thumb_image = pygame.image.fromstring(screenshot, size, "RGB").convert()
            thumb_rect = thumb_image.get_rect().fit(rect)
            thumb_image = pygame.transform.smoothscale(thumb_image, thumb_rect.size)
        else:
            thumb_rect = rect.copy()
            thumb_rect.width /= 5.0
            thumb_image = pygame.Surface(thumb_rect.size)
            thumb_image.fill((255, 255, 255))

        if "error" in save_data:
            red = (255,   0,   0)
            pygame.draw.line(thumb_image, red, [0, 0], thumb_rect.size, 3)
            pygame.draw.line(thumb_image, red, [0, thumb_rect.height], [thumb_rect.width, 0], 3)

        # Draw the screenshot
        slot_image.blit(thumb_image, (rect.width * .20, 0))

        # Draw the slot text
        rect = rect.move(0, rect.height // 2 - 10)
        text.draw_text(slot_image, T.translate('slot') + " " + str(slot_num), rect, font=self.font)

        x = int(rect.width * .5)
        text.draw_text(slot_image, save_data['player_name'], (x, 0, 500, 500), font=self.font)
        if "error" not in save_data:
            text.draw_text(slot_image, save_data['time'], (x, 50, 500, 500), font=self.font)

        return slot_image

    def save(self):
        logger.info("Saving!")
        try:
            save_data = save.get_save_data(
                local_session,
            )
            save.save(
                save_data,
                self.selected_index + 1,
            )
            save.slot_number = self.selected_index
        except Exception as e:
            raise
            logger.error("Unable to save game!!")
            logger.error(e)
            open_dialog(local_session, [T.translate('save_failure')])
        else:
            open_dialog(local_session, [T.translate('save_success')])


    def on_menu_selection(self, menuitem):
        def positive_answer():
            self.client.pop_state() # close confirmation menu
            self.client.pop_state() # close save menu

            self.save()

        def negative_answer():
            self.client.pop_state() # close confirmation menu

        def ask_confirmation():
            # open menu to confirm the save
            menu = self.client.push_state("Menu")
            menu.shrink_to_items = True

            # add choices
            yes = MenuItem(self.shadow_text(T.translate('save_overwrite')), None, None, positive_answer)
            no = MenuItem(self.shadow_text(T.translate('save_keep')), None, None, negative_answer)

            menu.add(yes)
            menu.add(no)

        save_data = save.load(self.selected_index + 1)
        if save_data:
            ask_confirmation()
        else:
            self.client.pop_state() # close save menu
            self.save()

