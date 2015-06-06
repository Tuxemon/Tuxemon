
import pygame
from core import prepare
from core.components.menu import Menu


class HpBar(object):

    def __init__(self, screen, monster=None, x=0, y=0, 
                 width=48, height=3, color=(112,248,168),
                 bar_position=(16,2), image="resources/gfx/ui/monster/hp_bar.png"):
        self.screen = screen
        self.monster = monster
        self.x = x
        self.y = y
        self.state = None
        self.color = color
        self.visible = True
        self.bar_position = bar_position

        # Load the hp bar ui.
        self.image = image
        self.surface = pygame.image.load(self.image).convert_alpha()
        self.surface = pygame.transform.scale(
            self.surface,
            (self.surface.get_width() * prepare.SCALE,
             self.surface.get_height() * prepare.SCALE))

        # Set the width and height of the hp bar.
        self.width = width * prepare.SCALE
        self.height = height * prepare.SCALE

        # Set the color of the HP bar.
        self.bar_surface = pygame.Surface((self.width, self.height))
        self.bar_surface.fill(color)
        self.set_health_percentage()

        # The player's health bar starts at pixel position 16,2
        self.current_bar_position = (
            self.x + (bar_position[0] * prepare.SCALE),
            self.y + (bar_position[1] * prepare.SCALE))


    def set_health_percentage(self):
        if self.monster:
            # Scale the monster's health bar based on how much health the monster has.
            health_percent = float(self.monster.current_hp) / float(self.monster.hp)
            self.bar_surface = pygame.transform.scale(
                self.bar_surface, (int(self.width * health_percent), self.height))


    def update(self):
        # Update the size of the bar based on health.
        self.set_health_percentage()

        # Update the position of the bar based on HP bar position.
        self.current_bar_position = (
            self.x + (self.bar_position[0] * prepare.SCALE),
            self.y + (self.bar_position[1] * prepare.SCALE))


    def draw(self):

        self.update()

        self.screen.blit(self.surface, (self.x, self.y))
        self.screen.blit(self.bar_surface, self.current_bar_position)

