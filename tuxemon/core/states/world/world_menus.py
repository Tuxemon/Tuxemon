from __future__ import division

import logging
from collections import OrderedDict
from functools import partial

import pygame

from core import prepare
from core.tools import open_dialog
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


def adapter(name, *args):
    from collections import namedtuple
    nt = namedtuple(name, "parameters")

    def func(*args):
        return nt(args)

    return func


class WorldMenuState(Menu):
    """
    Menu for the world state
    """

    def initialize_items(self):
        def change_state(state, **kwargs):
            return partial(self.game.replace_state, state, **kwargs)

        def exit_game():
            # TODO: API
            self.game.done = True
            self.game.exit = True

        def battle():
            self.game.pop_state(self)
            from core.components.event.actions.combat import Combat
            start_battle = partial(adapter("start_battle"))
            Combat().start_battle(self.game, start_battle(1))

        def not_implemented_dialog():
            open_dialog(self.game, ["This feature is not implemented."])

        # Main Menu - Allows users to open the main menu in game.
        self.menu_items_map = OrderedDict((
            ('JOURNAL', battle),
            ('TUXEMON', change_state("MonsterMenuState")),
            ('BAG', change_state("ItemMenuState")),
            ('PLAYER', not_implemented_dialog),
            ('SAVE', change_state("SaveMenuState")),
            ('LOAD', change_state("LoadMenuState")),
            ('OPTIONS', not_implemented_dialog),
            ('EXIT', exit_game)
        ))

        for label in self.menu_items_map.keys():
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, None)

    def on_menu_selection(self, menuitem):
        self.menu_items_map[menuitem.label]()

    def draw(self, surface):
        """ Draws the menu object to a pygame surface.

        :param surface: Surface to draw on
        :type surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        self.window.draw(surface, self.rect)

        if self.menu_items:
            self.menu_items.draw(surface)
            self.menu_sprites.draw(surface)

        self.sprites.draw(surface)

    def animate_open(self):
        self.state = "opening"  # required
        self._initialize_items()

        # position the menu off screen.  it will be slid into view with an animation
        w, h = prepare.SCREEN_SIZE
        self.rect = pygame.Rect(w, 0, w // 4, h)

        # animate the menu sliding in
        ani = self.animate(self.rect, x=w - self.rect.width, duration=.50)
        ani.callback = lambda: setattr(self, "state", "normal")
        return ani

    def animate_close(self):
        # animate the menu sliding out
        ani = self.animate(self.rect, x=prepare.SCREEN_SIZE[0], duration=.50)
        return ani
