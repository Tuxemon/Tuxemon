from __future__ import division

import logging
from functools import partial

import pygame

from core import tools
from core.components.locale import translator
from core.components.menu import PopUpMenu
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu
from core.components.sprite import SpriteGroup, MenuSpriteGroup
from core.components.technique import Technique
from core.components.ui.draw import GraphicBox

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class MainCombatMenuState(PopUpMenu):
    """
    Menu for the world state
    """
    escape_key_exits = False

    def initialize_items(self):
        def change_state(state, **kwargs):
            return partial(self.game.push_state, state, **kwargs)

        def run():
            self.game.pop_state(self)
            combat_state = self.game.get_state_name("CombatState")
            combat_state.remove_player(combat_state.players[0])

        menu_items_map = (
            ('menu_fight', self.open_technique_menu),
            ('menu_monster', self.open_swap_menu),
            ('menu_item', change_state("ItemMenuState")),
            ('menu_run', run)
        )

        for key, callback in menu_items_map:
            label = translator.translate(key).upper()
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, callback)

    def open_swap_menu(self):
        """ Open menus to swap monsters in party

        :return: None
        """

        def swap_it(menuitem):
            monster = menuitem.game_object
            trans = translator.translate
            if monster in self.game.get_state_name('CombatState').active_monsters:
                tools.open_dialog(self.game, [trans('combat_isactive', {"name": monster.name})])
                return
            elif monster.current_hp < 1:
                tools.open_dialog(self.game, [trans('combat_fainted', {"name": monster.name})])
            player = self.game.player1
            target = player.monsters[0]
            swap = Technique("technique_swap")
            swap.other = monster
            combat_state = self.game.get_state_name("CombatState")
            combat_state.enqueue_action(player, swap, target)
            self.game.pop_state()  # close technique menu
            self.game.pop_state()  # close the monster action menu

        menu = self.game.push_state("MonsterMenuState")
        menu.on_menu_selection = swap_it
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.game.screen.get_rect().right)
        menu.monster = self.monster

    def open_technique_menu(self):
        """ Open menus to choose a Technique to use

        :return: None
        """

        def choose_technique():
            # open menu to choose technique
            menu = self.game.push_state("Menu")
            menu.shrink_to_items = True

            # add techniques to the menu
            for tech in self.monster.moves:
                image = self.shadow_text(tech.name)
                item = MenuItem(image, None, None, tech)
                menu.add(item)

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.game.screen.get_rect().right)

            # set next menu after after selection is made
            menu.on_menu_selection = choose_target

        def choose_target(menu_item):
            # open menu to choose target of technique
            technique = menu_item.game_object
            state = self.game.push_state("CombatTargetMenuState")
            state.on_menu_selection = partial(enqueue_technique, technique)

        def enqueue_technique(technique, menu_item):
            # enqueue the technique
            target = menu_item.game_object
            combat_state = self.game.get_state_name("CombatState")
            combat_state.enqueue_action(self.monster, technique, target)

            # close all the open menus
            self.game.pop_state()  # close target chooser
            self.game.pop_state()  # close technique menu
            self.game.pop_state()  # close the monster action menu

        choose_technique()


class CombatTargetMenuState(Menu):
    """
    Menu for selecting targets of techniques and items

    This special menu draws over the combat screen
    """
    transparent = True

    def create_new_menu_items_group(self):
        # these groups will not automatically position the sprites
        self.menu_items = MenuSpriteGroup()
        self.menu_sprites = SpriteGroup()

    def startup(self, *args, **kwargs):
        super(CombatTargetMenuState, self).startup(*args, **kwargs)

        # load and scale the menu borders
        border = tools.load_and_scale(self.borders_filename)
        self.border = GraphicBox(border, None, None)

    def initialize_items(self):
        # get a ref to the combat state
        combat_state = self.game.get_state_name("CombatState")

        # TODO: trainer targeting
        # TODO: cleanup how monster sprites and whatnot are managed
        # get all the monster positions
        for player, monsters in combat_state.monsters_in_play.items():
            for monster in monsters:
                sprite = combat_state._monster_sprite_map[monster]
                item = MenuItem(None, None, None, monster)
                item.rect = sprite.rect.copy()
                center = item.rect.center
                item.rect.inflate_ip(tools.scale(16), tools.scale(16))
                item.rect.center = center
                yield item

    def on_menu_selection_change(self):
        # clear out the old borders
        for sprite in self.menu_items:
            sprite.image = None

        # find the selected item and make a border for it
        item = self.get_selected_item()
        if item:
            item.image = pygame.Surface(item.rect.size, pygame.SRCALPHA)
            self.border.draw(item.image)

    def select_optimal_default_target(self):
        """ Select the best default target for Techniques and Items

        :return:
        """
        pass

