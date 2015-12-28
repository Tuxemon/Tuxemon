import pygame
from core.components.menu import Menu

class BottomMenu(Menu):

    def __init__(self, screen, resolution, game, name="Bottom Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        # Adding static variables for menus for the bottom 1/2 of the screen
        # (mainly for states.combat)
        self.difference_x = ((resolution[0]/4))
        self.difference_y = ((resolution[1]/4))
        # Native resolution is similar to the old gameboy resolution. This is used for scaling.
        self.native_resolution = [240, 160]
        # Scaling the shit outa those menus!
        self.scale = int( (resolution[0] / self.native_resolution[0]) )
        for picture, border in self.border.items():
            self.border[picture] = pygame.transform.scale(border,
                (border.get_width() * self.scale, border.get_height() * self.scale) )
        self.difference = self.border["left-top"].get_width()

