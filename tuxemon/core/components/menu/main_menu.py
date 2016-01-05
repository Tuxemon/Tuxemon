import pygame
from core import prepare
from core.components.menu import Menu

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


class MainMenu(Menu):

    def __init__(self, screen, resolution, game, name="Main Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.first_run = True
        self.save = False
        self.state = "closed"
        self.visible = False
        '''
        self.menu_icons_paths = ['resources/gfx/ui/menu/journal.png',
                                 'resources/gfx/ui/menu/tuxemon.png',
                                 'resources/gfx/ui/menu/backpack.png',
                                 'resources/gfx/ui/menu/player.png',
                                 'resources/gfx/ui/menu/save.png',
                                 'resources/gfx/ui/menu/load.png',
                                 'resources/gfx/ui/menu/settings.png',
                                 'resources/gfx/ui/menu/exit.png',]

        # Load all the menu icon images
        for path in self.menu_icons_paths:
            icon_surface = pygame.image.load(path).convert_alpha()
            icon_surface = pygame.transform.scale(icon_surface,
            (icon_surface.get_width() * prepare.SCALE,
            icon_surface.get_height() * prepare.SCALE))
            self.menu_icons.append(icon_surface)
        '''
        self.menu_select_sound = mixer.Sound(
            prepare.BASEDIR + "resources/sounds/interface/" +
            "50561__broumbroum__sf3-sfx-menu-select.ogg")


    def get_event(self, event, game=None):

        if len(self.menu_items) > 0:
            self.line_spacing = (self.size_y / len(self.menu_items)) - self.font_size

        if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            self.selected_menu_item += 1
            if self.selected_menu_item > len(self.menu_items) - 1:
                self.selected_menu_item = 0

            self.menu_select_sound.play()

        if event.type == pygame.KEYUP and event.key == pygame.K_UP:
            self.selected_menu_item -= 1
            if self.selected_menu_item < 0:
                self.selected_menu_item = len(self.menu_items) - 1

            self.menu_select_sound.play()

        # If the player presses Enter while a menu item is selected
        if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
            self.menu_select_sound.play()

            if self.menu_items[self.selected_menu_item] == "JOURNAL":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
            elif self.menu_items[self.selected_menu_item] == "TUXEMON":
                self.game.monster_menu.visible = True
                self.game.monster_menu.interactable = True
                self.interactable = False
                self.state = "closing"
            elif self.menu_items[self.selected_menu_item] == "BAG":
                self.game.item_menu.visible = True
                self.game.item_menu.interactable = True
                self.interactable = False
                self.state = "closing"
            elif self.menu_items[self.selected_menu_item] == "PLAYER":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
            elif self.menu_items[self.selected_menu_item] == "SAVE":
                self.game.save_menu.visible = True
                self.game.save_menu.interactable = True
                self.interactable = False
                self.state = "closing"
            elif self.menu_items[self.selected_menu_item] == "LOAD":
                self.game.game.push_state('LOAD')
            elif self.menu_items[self.selected_menu_item] == "OPTIONS":
                self.game.not_implmeneted_menu.visible = True
                self.game.not_implmeneted_menu.interactable = True
            elif self.menu_items[self.selected_menu_item] == "EXIT":
                game.exit = True
                game.game.exit = True
