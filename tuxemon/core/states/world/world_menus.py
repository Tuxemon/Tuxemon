from __future__ import division

import logging
from collections import OrderedDict
from functools import partial

import pygame

from core import prepare
from core.tools import open_dialog
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu
from core.components.locale import translator

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
    shrink_to_items = True    # this menu will shrink, but size is adjusted when opened

    def initialize_items(self):
        trans = translator.translate
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
            open_dialog(self.game, [trans('not_implemented')])

        # Main Menu - Allows users to open the main menu in game.
        self.menu_items_map = OrderedDict((
            (trans('menu_journal').upper(), not_implemented_dialog),
            (trans('menu_monster').upper(), change_state("MonsterMenuState")),
            (trans('menu_bag').upper(), change_state("ItemMenuState")),
            (trans('menu_player').upper(), not_implemented_dialog),
            (trans('menu_save').upper(), change_state("SaveMenuState")),
            (trans('menu_load').upper(), change_state("LoadMenuState")),
            (trans('menu_options').upper(), not_implemented_dialog),
            (trans('exit').upper(), exit_game)
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

        # position the menu off screen.  it will be slid into view with an animation
        right, height = prepare.SCREEN_SIZE

        # TODO: more robust API for sizing (kivy esque?)
        # TODO: after menu "add" merge, this can be simplified
        # this is highly irregular:
        # shrink to get the final width
        # record the width
        # turn off shrink, then adjust size
        self.shrink_to_items = True     # force shrink of menu
        self.menu_items.expand = False  # force shrink of items
        self._initialize_items()        # re-add items, trigger layout
        width = self.rect.width         # store the ideal width

        self.shrink_to_items = False    # force shrink of menu
        self.menu_items.expand = True   # force shrink of items
        self._initialize_items()        # re-add items, trigger layout
        self.rect = pygame.Rect(right, 0, width, height)  # set new rect

        # animate the menu sliding in
        ani = self.animate(self.rect, x=right - width, duration=.50)
        ani.callback = lambda: setattr(self, "state", "normal")
        return ani

    def animate_close(self):
        # animate the menu sliding out
        ani = self.animate(self.rect, x=prepare.SCREEN_SIZE[0], duration=.50)
        return ani
