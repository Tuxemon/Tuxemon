import pygame
import os
import logging
from core.components.menu import Menu
from .. import save
from ... import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.menu.save_menu successfully imported")


class SaveMenu(Menu):

    def __init__(self, screen, resolution, game, name="Save Menu"):
        Menu.__init__(self, screen, resolution, game, name)

        self.slots = 3
        self.selected_menu_item = 0
        self.slot_surfaces = {}
        self.save_data = {}
        self.first_run = True

    def draw(self):

        # We can call the draw function from our parent "Menu" class,
        # and also draw some additional stuff specifically for the Save Menu.
        Menu.draw(self)

        self.slot_size = (self.size_y / self.slots)
        self.padding = (self.font_size * self.scale) / 3

        # Set the initial slot's position
        slot_pos_x = 0
        slot_pos_y = 0

        # Draw the different save slots
        for slot in range(self.slots):
            slot_num = slot + 1
            slot_name = "slot" + str(slot_num)

            # Check to see if a save exists for the current slot
            if os.path.exists(prepare.SAVE_PATH + str(slot_num) + ".png"):

                if slot_name not in self.slot_surfaces:
                    # Scale the slot image n shit
                    self.slot_surfaces[slot_name] = pygame.image.load(
                        prepare.SAVE_PATH + str(slot_num) + ".png").convert()
                    scale = float(self.slot_size) / float(self.slot_surfaces[slot_name].get_width())
                    width = self.slot_surfaces[slot_name].get_width()
                    height = self.slot_surfaces[slot_name].get_height()

                    thumb_width = self.slot_size
                    thumb_height = int(height * scale)

                    scale = int(width / self.slot_size)
                    self.slot_surfaces[slot_name] = pygame.transform.scale(
                        self.slot_surfaces[slot_name], (thumb_width, thumb_height))
                else:
                    thumb_width = self.slot_surfaces[slot_name].get_width()
                    thumb_height = self.slot_surfaces[slot_name].get_height()

                # Draw the screenshot
                thumb_x = self.pos_x
                thumb_y = self.pos_y + slot_pos_y + int(self.font_size * 1.5)
                self.screen.blit(self.slot_surfaces[slot_name],
                                 (thumb_x, thumb_y))

                # Try and load the save game and draw details about the save
                try:
                    save_data = save.load(slot_num)
                except Exception as e:
                    logger.error(e)
                    save_data = {}
                    save_data["error"] = "Save file corrupted"
                    logger.error("Failed loading save file.")

                if "error" not in save_data:
                    self.draw_text(save_data['player_name'],
                                   thumb_width + self.padding,
                                   slot_pos_y + int(self.font_size * 1.5))
                    self.draw_text(save_data['time'],
                                   thumb_width + self.padding,
                                   slot_pos_y + (self.font_size * 3.5) +
                                   self.padding)

            # If a save game does not exist, show empty slot
            else:
                self.draw_text("empty slot", self.size_x / 3, slot_pos_y + (self.slot_size / 2))

            # Draw the slot text
            self.draw_text("Slot " + str(slot_num), slot_pos_x, slot_pos_y)

            # If the slot is selected, draw a rectangle around it
            if slot == self.selected_menu_item:
                pygame.draw.rect(self.screen, (147, 112, 219), (self.pos_x - self.padding,
                                                                self.pos_y + slot_pos_y - self.padding,
                                                                self.size_x + (self.padding*2),
                                                                self.slot_size), 2)

            slot_pos_y += self.slot_size

    def get_event(self, event):
        # Handle key events when the menu is visible
        if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > self.slots - 1:
                self.selected_menu_item = 0

        if event.type == pygame.KEYUP and event.key == pygame.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 0:
                self.selected_menu_item = self.slots - 1

        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            logger.info("Closing save menu!")
            self.visible = False
            self.interactable = False
            self.first_run = True
            self.game.main_menu.interactable = True

        if event.type == pygame.KEYUP and event.key == pygame.K_RETURN and not self.first_run:
            logger.info("Saving!")
            # Save the game!!
            try:
                save.save(self.save_data['player'],
                          self.selected_menu_item + 1,
                          self.game)
                del self.slot_surfaces["slot" + str(self.selected_menu_item + 1)]
            except Exception as e:
                logger.error("Unable to save game!!")
                logger.error(e)

            if self.visible:
                self.visible = False
                self.interactable = False
                self.first_run = True
                self.game.main_menu.interactable = True
                self.game.main_menu.visible = True
                self.game.main_menu.state = "opening"
            else:
                self.visible = True

        if self.visible:
            self.first_run = False
