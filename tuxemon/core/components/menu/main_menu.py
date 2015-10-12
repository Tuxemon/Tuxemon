import pygame
from core import tools, prepare
from core.components.menu import NewMenu

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer

class MainMenu(NewMenu):

    def __init__(self, game, name="Main Menu"):

        # Initialize the parent menu class's default shit
        NewMenu.__init__(self, game, name=name)
        self.first_run = True
        self.save = False
        self.menu_state = "closed"
        self.visible = False

        self.menu_select_sound = mixer.Sound(
            prepare.BASEDIR + "resources/sounds/interface/50561__broumbroum__sf3-sfx-menu-select.ogg")

        # Used to calculate menu position
        resolution = prepare.SCREEN_SIZE
        fifth_screen_width = tools.get_pos_from_percent('20%', resolution[0])
        sixth_screen_width = int(resolution[0] / 6)

        # The main menu will be positioned on the right-hand side of the
        # screen and be about 1/5th the width of the window.
        x = (sixth_screen_width * 5) - (self.border_thickness * 2)
        y = self.border_thickness

        # Set up our open and closed positions
        self.open_position = (x, y)
        self.closed_position = (x + self.width + (self.border_thickness * 2), y)
        self.set_position(self.closed_position[0], self.closed_position[1])

        # Set the size of our main menu
        width = fifth_screen_width
        height = resolution[1] - (self.border_thickness * 2)
        self.set_size(width, height)

        # By default, set menu to invisible and non-interactable
        self.set_visible(False)
        self.set_interactable(False)

        # Set our default menu items
        menu_items = ["JOURNAL", "TUXEMON", "BAG", "PLAYER",
                      "SAVE", "LOAD", "OPTIONS", "EXIT"]
        self.set_text_menu_items(menu_items, align="middle", justify="center")

    def get_event(self, event):

        if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            self.menu_select_down()
            self.menu_select_sound.play()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self.menu_select_up()
            self.menu_select_sound.play()


        # If the player presses Enter while a menu item is selected
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.menu_select_sound.play()

            world = self.game.state_dict["WORLD"]
            selected_item = self.get_current_selection()

            if selected_item == "JOURNAL":
                world.not_implmeneted_menu.visible = True
                world.not_implmeneted_menu.interactable = True
            elif selected_item == "TUXEMON":
                world.monster_menu.visible = True
                world.monster_menu.interactable = True
                self.set_interactable(False)
                self.state = "closing"
            elif selected_item == "BAG":
                world.item_menu.visible = True
                world.item_menu.interactable = True
                self.set_interactable(False)
                self.state = "closing"
            elif selected_item == "PLAYER":
                world.not_implmeneted_menu.set_visible(True)
                world.not_implmeneted_menu.set_interactable(True)
            elif selected_item == "SAVE":
                world.save_menu.visible = True
                world.save_menu.interactable = True
                self.set_interactable(False)
                self.state = "closing"
            elif selected_item == "LOAD":
                world.not_implmeneted_menu.visible = True
                world.not_implmeneted_menu.interactable = True
            elif selected_item == "OPTIONS":
                world.not_implmeneted_menu.set_visible(True)
                world.not_implmeneted_menu.set_interactable(True)
            elif selected_item == "EXIT":
                world.exit = True
                self.game.exit = True


