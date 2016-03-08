import pygame

from core import tools
from core.components.ui.draw import GraphicBox


class HpBar(object):
    """ HP bar for UI elements.

    """
    border_filename = "gfx/ui/monster/hp_bar.png"
    border = None

    def __init__(self, value=1.0):
        super(HpBar, self).__init__()

        if self.border is None:
            self.load_graphics()

        rect = (0, 0, 100, 40)
        self.rect = rect
        # self._color = 112, 248, 168
        self.fg_color = 10, 240, 25
        self.bg_color = 245, 10, 25
        self.value = value
        self.visible = True

    def load_graphics(self):
        """ Image become class attribute, so is shared.
            Eventually, implement some game-wide image caching
        """
        image = tools.load_and_scale(self.border_filename)
        HpBar.border = GraphicBox(image)

    @staticmethod
    def calc_inner_rect(rect):
        """ Calculate the inner rect to draw fg_color that fills bar
            The values here are calculated based on game scale and
            the content of the border image file.

        :param rect:
        :returns:
        """
        inner = rect.copy()
        inner.top += tools.scale(2)
        inner.height -= tools.scale(4)
        inner.left += tools.scale(9)
        inner.width -= tools.scale(11)
        return inner

    def draw(self, surface, rect):
        inner = self.calc_inner_rect(rect)
        pygame.draw.rect(surface, self.bg_color, inner)
        if self.value > 0:
            left = inner.left
            inner.width *= self.value
            inner.left = left
            pygame.draw.rect(surface, self.fg_color, inner)
        self.border.draw(surface, rect)


class MenuItem(pygame.sprite.Sprite):
    def __init__(self, image, label, description, game_object):
        super(MenuItem, self).__init__()
        self.image = image
        if image:
            self.rect = image.get_rect()
        self.label = label
        self.description = description
        self.game_object = game_object

        self._in_focus = False

    def toggle_focus(self):
        self._in_focus = not self._in_focus

    @property
    def in_focus(self):
        return self._in_focus

    @in_focus.setter
    def in_focus(self, value):
        self._in_focus = bool(value)


class MenuCursor(pygame.sprite.Sprite):
    def __init__(self, image):
        super(MenuCursor, self).__init__()
        self.image = image
        self.rect = image.get_rect()
