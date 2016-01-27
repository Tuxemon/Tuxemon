import pygame as pg
import logging
from collections import namedtuple
from core import prepare
from core.components import save
from core.components.menu import Menu
from core.components.menu.save_menu import SaveMenu
from core.components.event.actions import player

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.menu.load_menu successfully imported")


class LoadMenu(SaveMenu):

    def __init__(self, screen, resolution, game, name="Load Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        SaveMenu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay

    def get_event(self, event=None, game=None):

        if event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
            if self.game.current_state == "WORLD":
                self.game.main_menu.interactable = True
                self.game.main_menu.visible = True
                self.game.main_menu.state = "opening"
                self.game.pop_state()
            else:
                self.game.pop_state()

        # Copy pasta from save, updown stuff
        if event.type == pg.KEYUP and event.key == pg.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > self.slots - 1:
                self.selected_menu_item = 0

        if event.type == pg.KEYUP and event.key == pg.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 0:
                self.selected_menu_item = self.slots - 1

        # If the player presses Enter while a menu item is selected
        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            '''if self.menu_items[self.selected_menu_item] == "NEW GAME":
                self.game.push_state("WORLD")
                self.game.player1 = prepare.player1
                self.game.pop_state(1)'''
            try:
                save_data = save.load(self.selected_menu_item + 1)
            except Exception as e:
                logger.error(e)
                save_data = {}
                save_data["error"] = "Save file corrupted"
                logger.error("Failed loading save file.")
            if "error" not in save_data:
                statepoppin = self.game.current_state
                self.save_data = save.load(self.selected_menu_item + 1)
                self.game.player1 = prepare.player1
                self.game.player1.game_variables = save_data['game_variables']
                self.game.player1.tile_pos = save_data['tile_pos']
                self.game.player1.inventory = save_data['inventory']
                self.game.player1.monsters = save_data['monsters']
                self.game.player1.storage = save_data['storage']
                self.game.player1.name = save_data['player_name']
                self.game.push_state("WORLD")
                tele_x = str(int(save_data['tile_pos'][0]))
                tele_y = str(int(save_data['tile_pos'][1]))
                Action = namedtuple("action", ["type", "parameters"])
                action = Action("teleport", [save_data['current_map'], tele_x, tele_y])
                self.game.event_engine.actions['teleport']['method'](self.game, action)
                self.game.pop_state(statepoppin)

    def draw(self):
        SaveMenu.draw(self)
