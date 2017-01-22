from __future__ import division

import logging
import os

import pygame

from core import prepare
from core.tools import open_dialog
from core.components import save
from core.components.menu import PopUpMenu
from core.components.menu.interface import MenuItem
from core.components.ui import text
from core.components.locale import translator
trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


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
        text.draw_text(slot_image, trans('empty_slot').title(), rect, font=self.font)
        return slot_image

    def render_slot(self, rect, slot_num):
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)

        thumb_image = None
        try:
            thumb_image = pygame.image.load(prepare.SAVE_PATH + str(slot_num) + ".png").convert()
            thumb_rect = thumb_image.get_rect().fit(rect)
            thumb_image = pygame.transform.smoothscale(thumb_image, thumb_rect.size)
        except Exception as e:
            logger.error(e)

        # Try and load the save game and draw details about the save
        try:
            save_data = save.load(slot_num)
        except Exception as e:
            logger.error(e)
            save_data = dict()
            save_data["error"] = "Save file corrupted"
            save_data["player_name"] = "BROKEN SAVE!"
            logger.error("Failed loading save file.")
            if thumb_image is not None:
                pygame.draw.line(thumb_image, (255,   0,   0), [0, 0], thumb_rect.size, 3)
                pygame.draw.line(thumb_image, (255,   0,   0), [0, thumb_rect.height], [thumb_rect.width, 0], 3)

        # Draw the screenshot
        if thumb_image is not None:
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
            save.save(self.game.player1,
                      self.capture_screenshot(),
                      self.selected_index + 1,
                      self.game)
        except Exception as e:
            logger.error("Unable to save game!!")
            logger.error(e)
            print(e)

            open_dialog(self.game, [trans('save_failure')])
            self.game.pop_state(self)
        else:
            open_dialog(self.game, [trans('save_success')])
            self.game.pop_state(self)

    def capture_screenshot(self):
        screenshot = pygame.Surface(self.game.screen.get_size())
        world = self.game.get_state_name("WorldState")
        world.draw(screenshot)
        return screenshot
