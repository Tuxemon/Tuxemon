import pygame as pg
from core import prepare
from core.components.menu import Menu


class StartMenu(Menu):

    def __init__(self, screen, resolution, game, name="Start Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)

    def get_event(self, event, game=None):

        # If the player presses Enter while a menu item is selected
        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            if self.menu_items[self.selected_menu_item] == "NEW GAME":
                self.game.push_state("WORLD")
                self.game.player1 = prepare.player1
                self.game.pop_state(1)
            elif self.menu_items[self.selected_menu_item] == "LOAD":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
            elif self.menu_items[self.selected_menu_item] == "OPTIONS":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
            elif self.menu_items[self.selected_menu_item] == "EXIT":
                self.game.exit = True
