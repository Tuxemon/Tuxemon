from core import prepare
from core.components.menu import Menu


class StartMenu(Menu):

    def __init__(self, screen, resolution, game, name="Start Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay

    def get_event(self, event=None, game=None):

        # If the player presses Enter while a menu item is selected
        if self.menu_items[self.selected_menu_item] == "NEW GAME":
            statepoppin = (self.game.current_state)
            self.game.push_state("WORLD")
            self.game.player1 = prepare.player1
            self.game.pop_state(statepoppin)
        elif self.menu_items[self.selected_menu_item] == "LOAD":
            self.game.push_state("LOAD")
        elif self.menu_items[self.selected_menu_item] == "OPTIONS":
            return False
        elif self.menu_items[self.selected_menu_item] == "EXIT":
            self.game.exit = True
