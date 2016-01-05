from core.components.menu import Menu


class OptionsMenu(Menu):

    def __init__(self, screen, resolution, game, name="Options Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay

    def get_event(self, event=None, game=None):

        # If the player presses Enter while a menu item is selected
        if self.menu_items[self.selected_menu_item] == "NOT IMPLEMENTED":
            return False
        elif self.menu_items[self.selected_menu_item] == "BACK":
            self.game.pop_state()
