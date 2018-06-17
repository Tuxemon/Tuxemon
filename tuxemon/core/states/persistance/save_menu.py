from __future__ import division

import base64
import logging
import os

import pygame

from tuxemon.core import prepare
from tuxemon.core.tools import open_dialog
from tuxemon.core.components import save
from tuxemon.core.components.menu import PopUpMenu
from tuxemon.core.components.menu.interface import MenuItem
from tuxemon.core.components.ui import text
from tuxemon.core.components.locale import translator
trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class SaveMenuState(PopUpMenu):
    number_of_slots = 3
    shrink_to_items = True

    def initialize_items(self):
        empty_image = None
        rect = self.game.screen.get_rect()
        slot_rect = pygame.Rect(0, 0, rect.width * 0.80, rect.height // 6)
        for i in range(self.number_of_slots):
            # Check to see if a save exists for the current slot
            if os.path.exists(prepare.SAVE_PATH + str(i + 1) + ".save"):
                image = self.render_slot(slot_rect, i + 1)
                item = MenuItem(image, trans('menu_save'), None, None)
                self.add(item)
            else:
                if not empty_image:
                    empty_image = self.render_empty_slot(slot_rect)
                item = MenuItem(empty_image, "SAVE", None, None)
                self.add(item)

    def render_empty_slot(self, rect):
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)
        rect = rect.move(0, rect.height // 2 - 10)
        text.draw_text(slot_image, trans('empty_slot'), rect, font=self.font)
        return slot_image

    def render_slot(self, rect, slot_num):
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)

        # Try and load the save game and draw details about the save
        try:
            save_data = save.load(slot_num)
        except Exception as e:
            logger.error(e)
            save_data = dict()
            save_data["error"] = "Save file corrupted"
            save_data["player_name"] = "BROKEN SAVE!"
            logger.error("Failed loading save file.")

        if "screenshot" in save_data:
            screenshot = base64.decodestring(save_data["screenshot"])
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
        text.draw_text(slot_image, trans('slot') + " " + str(slot_num), rect, font=self.font)

        x = int(rect.width * .5)
        text.draw_text(slot_image, save_data['player_name'], (x, 0, 500, 500), font=self.font)
        if "error" not in save_data:
            text.draw_text(slot_image, save_data['time'], (x, 50, 500, 500), font=self.font)

        return slot_image

    def on_menu_selection(self, menuitem):
        logger.info("Saving!")
        try:
            save_data = save.get_save_data(
                self.game,
            )
            save.save(
                save_data,
                self.selected_index + 1,
            )
        except Exception as e:
            logger.error("Unable to save game!!")
            logger.error(e)
            open_dialog(self.game, [trans('save_failure')])
        else:
            open_dialog(self.game, [trans('save_success')])

        self.game.pop_state(self)

