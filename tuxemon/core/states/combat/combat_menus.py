from __future__ import division

import logging
from collections import OrderedDict
from functools import partial

from core.components.menu import PopUpMenu
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu
from core.components.monster import Technique

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class TechniqueMenuState(Menu):
    """
    Menu for the world state

    only suitable for single player ATM

    """
    shrink_to_items = True

    def initialize_items(self):
        for tech in self.monster.moves:
            image = self.shadow_text(tech.name)
            yield MenuItem(image, tech.name, None, tech)


class MainCombatMenuState(PopUpMenu):
    """
    Menu for the world state
    """
    escape_key_exits = False

    def initialize_items(self):
        self.monster = self.monster  # hack: to quiet pycharm warnings

        def change_state(state, **kwargs):
            return partial(self.game.push_state, state, **kwargs)

        def run():
            self.game.pop_state(self)
            combat_state.remove_player(combat_state.players[0])

        # hack for now
        combat_state = self.game.get_state_name("CombatState")

        self.menu_items_map = OrderedDict((
            ('FIGHT', self.open_technique_menu),
            ('TUXEMON', self.open_swap_menu),
            ('ITEM', change_state("ItemMenuState")),
            ('RUN', run)
        ))

        for label in self.menu_items_map.keys():
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, None)

    def on_menu_selection(self, menuitem):
        self.menu_items_map[menuitem.label]()

    def open_swap_menu(self):
        def swap_it(menuitem):
            monster = menuitem.game_object
            player = self.game.player1
            target = player.monsters[0]
            swap = Technique("Swap")
            swap.other = monster
            combat_state = self.game.get_state_name("CombatState")
            combat_state.enqueue_action(player, swap, target)
            self.game.pop_state()  # close technique menu
            self.game.pop_state()  # close the monster action menu

        state = self.game.push_state("MonsterMenuState")
        state.on_menu_selection = swap_it
        state.anchor("bottom", self.rect.top)
        state.anchor("right", self.game.screen.get_rect().right)
        state.monster = self.monster

    def open_technique_menu(self):
        def do_the_thing(menuitem):
            technique = menuitem.game_object
            combat_state = self.game.get_state_name("CombatState")

            # TODO: select target
            target = combat_state.players[1].monsters[0]
            combat_state.enqueue_action(self.monster, technique, target)
            self.game.pop_state()  # close technique menu
            self.game.pop_state()  # close the monster action menu

        state = self.game.push_state("TechniqueMenuState")
        state.on_menu_selection = do_the_thing
        state.anchor("bottom", self.rect.top)
        state.anchor("right", self.game.screen.get_rect().right)
        state.monster = self.monster
