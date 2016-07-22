from __future__ import division

import logging
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
    animate_contents = True

    def startup(self, *args, **kwargs):
        super(WorldMenuState, self).startup(*args, **kwargs)

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
        menu_items_map = (
            ('menu_journal', not_implemented_dialog),
            ('menu_monster', change_state("MonsterMenuState")),
            ('menu_bag', change_state("ItemMenuState")),
            ('menu_player', not_implemented_dialog),
            ('menu_save', change_state("SaveMenuState")),
            ('menu_load', change_state("LoadMenuState")),
            ('menu_options', not_implemented_dialog),
            ('exit', exit_game)
        )

        for key, callback in menu_items_map:
            label = translator.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)

    def animate_open(self):
        """ Animate the menu sliding in

        :return:
        """
        self.state = "opening"  # required

        # position the menu off screen.  it will be slid into view with an animation
        right, height = prepare.SCREEN_SIZE

        # TODO: more robust API for sizing (kivy esque?)
        # this is highly irregular:
        # shrink to get the final width
        # record the width
        # turn off shrink, then adjust size
        self.shrink_to_items = True     # force shrink of menu
        self.menu_items.expand = False  # force shrink of items
        self.refresh_layout()           # rearrange items
        width = self.rect.width         # store the ideal width

        self.shrink_to_items = False    # force shrink of menu
        self.menu_items.expand = True   # force shrink of items
        self.refresh_layout()           # rearrange items
        self.rect = pygame.Rect(right, 0, width, height)  # set new rect

        # animate the menu sliding in
        ani = self.animate(self.rect, x=right - width, duration=.50)
        ani.callback = lambda: setattr(self, "state", "normal")
        return ani

    def animate_close(self):
        """ Animate the menu sliding out

        :return:
        """
        ani = self.animate(self.rect, x=prepare.SCREEN_SIZE[0], duration=.50)
        return ani
