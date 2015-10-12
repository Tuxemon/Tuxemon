
import pygame
from core.components.menu import NewMenu


class DialogMenu(NewMenu):

    def __init__(self, game, size=(100, 100), position=(100, 100),
                 name="Dialog menu"):

        # Initialize the parent menu class's default shit
        NewMenu.__init__(self, game, size, position, name=name,
                         visible=False, interactable=False)
        self.delay = 0.5
        self.elapsed_time = self.delay

        # Set up our menu's default position.
        from core import prepare, tools
        resolution = prepare.SCREEN_SIZE
        half_screen_width = tools.get_pos_from_percent('50%', resolution[0])
        half_screen_height = tools.get_pos_from_percent('50%', resolution[1])
        quart_screen_width = tools.get_pos_from_percent('25%', resolution[0])
        quart_screen_height = tools.get_pos_from_percent('25%', resolution[1])

        self.set_size(half_screen_width - self.border_thickness,
                      quart_screen_height)

        x = half_screen_width - (self.width / 2) - (self.border_thickness * 2)
        y = (quart_screen_height * 3) - self.border_thickness
        self.set_position(x, y)

    def get_event(self, event):

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:

            # Hide the menu
            self.visible = False

            # Reset our elapsed time this menu is closed to zero
            self.elapsed_time = 0.0
