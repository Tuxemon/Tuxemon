import logging
from collections import defaultdict
from functools import partial

import pygame

from tuxemon.core import tools, graphics
from tuxemon.core.locale import T
from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import Menu
from tuxemon.core.menu.menu import PopUpMenu
from tuxemon.core.session import local_session
from tuxemon.core.sprite import MenuSpriteGroup, SpriteGroup
from tuxemon.core.technique import Technique
from tuxemon.core.ui.draw import GraphicBox

logger = logging.getLogger(__name__)


class MainCombatMenuState(PopUpMenu):
    """
    Main menu for combat: Fight, Item, Swap, Run

    TODO: there needs to be more general use registers in the combat state to query
          what player is doing what.  there's lots of spaghetti right now.
    """
    escape_key_exits = False

    def initialize_items(self):
        menu_items_map = (
            ('menu_fight', self.open_technique_menu),
            ('menu_monster', self.open_swap_menu),
            ('menu_item', self.open_item_menu),
            ('menu_run', self.run)
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, callback)

    def run(self):
        """ Cause player to run from the battle

        TODO: only works for player0

        :return: None
        """

        # TODO: only works for player0
        self.client.pop_state(self)
        combat_state = self.client.get_state_by_name("CombatState")

        if combat_state.is_trainer_battle:
            def open_menu():
                combat_state.task(
                    partial(combat_state.show_monster_action_menu, self.monster),
                    1
                )
            combat_state.alert(T.translate("combat_can't_run_from_trainer"), open_menu)
        else:
            combat_state.trigger_player_run(combat_state.players[0])

    def open_swap_menu(self):
        """ Open menus to swap monsters in party

        :return: None
        """

        def swap_it(menuitem):
            monster = menuitem.game_object

            if monster in self.client.get_state_by_name('CombatState').active_monsters:
                tools.open_dialog(local_session, [T.format('combat_isactive', {"name": monster.name})])
                return
            elif monster.current_hp < 1:
                tools.open_dialog(local_session, [T.format('combat_fainted', {"name": monster.name})])
                return
            combat_state = self.client.get_state_by_name("CombatState")
            swap = Technique("swap")
            swap.combat_state = combat_state
            player = local_session.player
            target = monster
            combat_state.enqueue_action(player, swap, target)
            self.client.pop_state()  # close technique menu
            self.client.pop_state()  # close the monster action menu

        menu = self.client.push_state("MonsterMenuState")
        menu.on_menu_selection = swap_it
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.client.screen.get_rect().right)
        menu.monster = self.monster

    def open_item_menu(self):
        """ Open menu to choose item to use

        :return:
        """

        def choose_item():
            # open menu to choose item
            menu = self.client.push_state("ItemMenuState")

            # set next menu after after selection is made
            menu.on_menu_selection = choose_target

        def choose_target(menu_item):
            # open menu to choose target of item
            item = menu_item.game_object
            self.client.pop_state()   # close the item menu
            # TODO: don't hardcode to player0
            combat_state = self.client.get_state_by_name("CombatState")
            state = self.client.push_state("CombatTargetMenuState", player=combat_state.players[0],
                                           user=combat_state.players[0], action=item)
            state.on_menu_selection = partial(enqueue_item, item)

        def enqueue_item(item, menu_item):
            target = menu_item.game_object
            # is the item valid to use?
            if not item.validate(target):
                msg = T.format('cannot_use_item_monster', {'name': item.name})
                tools.open_dialog(local_session, [msg])
                return

            # enqueue the item
            combat_state = self.client.get_state_by_name("CombatState")
            # TODO: don't hardcode to player0
            combat_state.enqueue_action(combat_state.players[0], item, target)

            # close all the open menus
            self.client.pop_state()  # close target chooser
            self.client.pop_state()  # close the monster action menu

        choose_item()

    def open_technique_menu(self):
        """ Open menus to choose a Technique to use

        :return: None
        """

        def choose_technique():
            # open menu to choose technique
            menu = self.client.push_state("Menu")
            menu.shrink_to_items = True

            # add techniques to the menu
            for tech in self.monster.moves:
                if tech.next_use <= 0:
                    image = self.shadow_text(tech.name)
                else:
                    image = self.shadow_text("%s %d" % (tech.name, abs(tech.next_use)), fg=self.unavailable_color)
                item = MenuItem(image, None, None, tech)
                menu.add(item)

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.client.screen.get_rect().right)

            # set next menu after after selection is made
            menu.on_menu_selection = choose_target

        def choose_target(menu_item):
            # open menu to choose target of technique
            technique = menu_item.game_object
            if technique.next_use > 0:
                params = {"move": technique.name, "name": self.monster.name}
                tools.open_dialog(local_session, [T.format('combat_recharging', params)])
                return

            combat_state = self.client.get_state_by_name("CombatState")
            state = self.client.push_state("CombatTargetMenuState", player=combat_state.players[0],
                                           user=self.monster, action=technique)
            state.on_menu_selection = partial(enqueue_technique, technique)

        def enqueue_technique(technique, menu_item):
            # enqueue the technique
            target = menu_item.game_object
            combat_state = self.client.get_state_by_name("CombatState")
            combat_state.enqueue_action(self.monster, technique, target)

            # close all the open menus
            self.client.pop_state()  # close target chooser
            self.client.pop_state()  # close technique menu
            self.client.pop_state()  # close the monster action menu

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
        super().startup(*args, **kwargs)

        # used to determine how player can target techniques
        self.user = kwargs.get("user")
        self.action = kwargs.get("action")
        self.player = kwargs.get("player")

        # load and scale the menu borders
        border = graphics.load_and_scale(self.borders_filename)
        self.border = GraphicBox(border, None, None)

    def initialize_items(self):
        # get a ref to the combat state
        combat_state = self.client.get_state_by_name("CombatState")

        # TODO: trainer targeting
        # TODO: cleanup how monster sprites and whatnot are managed
        # TODO: This is going to work fine for simple matches, but controls will be wonky for parties
        # TODO: (cont.) Need better handling of cursor keys for 2d layouts of menu items
        # get all the monster positions

        # this is used to determine who owns what monsters and what not
        # TODO: make less duplication of game data in memory, let combat state have more registers, etc
        self.targeting_map = defaultdict(list)

        for player, monsters in combat_state.monsters_in_play.items():
            for monster in monsters:

                # TODO: more targeting classes
                if player == self.player:
                    targeting_class = "own monster"
                else:
                    targeting_class = "enemy monster"

                self.targeting_map[targeting_class].append(monster)

                # TODO: handle odd cases where a situation creates no valid targets
                # if this target type is not handled by this action, then skip it
                if targeting_class not in self.action.target:
                    continue

                # inspect the monster sprite and make a border image for it
                sprite = combat_state._monster_sprite_map[monster]
                item = MenuItem(None, None, None, monster)
                item.rect = sprite.rect.copy()
                center = item.rect.center
                item.rect.inflate_ip(tools.scale(16), tools.scale(16))
                item.rect.center = center

                yield item

    def refresh_layout(self):
        """ Before refreshing the layout, determine the optimal target

        :return:
        """

        def determine_target():
            for tag in self.action.target:
                for target in self.targeting_map[tag]:
                    menu_item = self.search_items(target)
                    if menu_item.enabled:
                        # TODO: some API for this mess
                        # get the index of the menu_item
                        # change it
                        index = self.menu_items._spritelist.index(menu_item)
                        self.selected_index = index
                        return

        determine_target()
        super().refresh_layout()

    def on_menu_selection_change(self):
        """ Draw borders around sprites when selection changes

        :return:
        """
        # clear out the old borders
        for sprite in self.menu_items:
            sprite.image = None

        # find the selected item and make a border for it
        item = self.get_selected_item()
        if item:
            item.image = pygame.Surface(item.rect.size, pygame.SRCALPHA)
            self.border.draw(item.image)
