# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, Optional

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import combat, graphics, prepare, tools
from tuxemon.db import State, TechSort
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.monster import Monster
from tuxemon.sprite import SpriteGroup, VisualSpriteList
from tuxemon.states.items.item_menu import ItemMenuState
from tuxemon.states.monster import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], None]


class MainCombatMenuState(PopUpMenu[MenuGameObj]):
    """
    Main menu for combat: Fight, Item, Swap, Run

    TODO: there needs to be more general use registers in the combat state to
    query what player is doing what. There's lots of spaghetti right now.
    """

    escape_key_exits = False
    columns = 2

    def __init__(
        self, session: Session, cmb: CombatState, monster: Monster
    ) -> None:
        super().__init__()
        self.rect = self.calculate_menu_rectangle()
        assert monster.owner
        self.session = session
        self.combat = cmb
        self.character = monster.owner
        self.monster = monster
        self.party = cmb.monsters_in_play[self.character]
        if self.character == cmb.players[0]:
            self.enemy = cmb.players[1]
            self.opponents = cmb.monsters_in_play[self.enemy]
        if self.character == cmb.players[1]:
            self.enemy = cmb.players[0]
            self.opponents = cmb.monsters_in_play[self.enemy]
        self.menu_visibility = {
            "menu_fight": True,
            "menu_monster": True,
            "menu_item": True,
            "menu_forfeit": self.enemy.forfeit,
            "menu_run": True,
        }

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = self.client.screen.get_rect()
        menu_width = rect_screen.w // 2.5
        menu_height = rect_screen.h // 4
        rect = Rect(0, 0, menu_width, menu_height)
        rect.bottomright = rect_screen.w, rect_screen.h
        return rect

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        common_menu_items = (
            ("menu_fight", self.open_technique_menu),
            ("menu_monster", self.open_swap_menu),
            ("menu_item", self.open_item_menu),
        )

        if self.combat.is_trainer_battle:
            menu_items_map = common_menu_items + (
                ("menu_forfeit", self.forfeit),
            )
        else:
            menu_items_map = common_menu_items + (("menu_run", self.run),)

        for key, callback in menu_items_map:
            foreground = (
                self.unavailable_color
                if not self.menu_visibility[key]
                else None
            )
            yield MenuItem(
                self.shadow_text(T.translate(key).upper(), fg=foreground),
                T.translate(key).upper(),
                None,
                callback,
                self.menu_visibility[key],
            )

    def update_menu_visibility(self, key: str, visible: bool) -> None:
        if key in self.menu_visibility:
            self.menu_visibility[key] = visible
        else:
            raise ValueError(f"Invalid menu item key: {key}")

    def forfeit(self) -> None:
        """
        Cause player to forfeit from the trainer battles.
        """
        forfeit = Technique.create("menu_forfeit")
        forfeit.combat_state = self.combat
        self.client.remove_state_by_name("MainCombatMenuState")
        self.combat.enqueue_action(self.party[0], forfeit, self.opponents[0])

    def run(self) -> None:
        """
        Cause player to run from the wild encounters.
        """
        run = Technique.create("menu_run")
        run.combat_state = self.combat
        if not run.validate_monster(self.session, self.monster):
            params = {
                "monster": self.monster.name.upper(),
                "status": self.monster.status[0].name.lower(),
            }
            msg = T.format("combat_player_run_status", params)
            tools.open_dialog(self.client, [msg])
            return
        self.client.remove_state_by_name("MainCombatMenuState")
        self.combat.enqueue_action(self.party[0], run, self.opponents[0])

    def open_swap_menu(self) -> None:
        """Open menus to swap monsters in party."""

        def swap_it(menuitem: MenuItem[Monster]) -> None:
            added = menuitem.game_object
            swap = Technique.create("swap")
            swap.combat_state = self.combat
            if not swap.validate_monster(self.session, self.monster):
                params = {
                    "monster": self.monster.name.upper(),
                    "status": self.monster.status[0].name.lower(),
                }
                msg = T.format("combat_player_swap_status", params)
                tools.open_dialog(self.client, [msg])
                return
            self.combat.enqueue_action(self.monster, swap, added)
            self.client.remove_state_by_name("MonsterMenuState")
            self.client.remove_state_by_name("MainCombatMenuState")

        def validate_monster(menu_item: Monster) -> bool:
            if combat.fainted(menu_item):
                return False
            if menu_item in self.combat.active_monsters:
                return False
            return True

        def validate(menu_item: MenuItem[Monster]) -> bool:
            if isinstance(menu_item, Monster):
                return validate_monster(menu_item)
            return False

        menu = self.client.push_state(MonsterMenuState(self.character))
        menu.on_menu_selection = swap_it  # type: ignore[assignment]
        menu.is_valid_entry = validate  # type: ignore[assignment]
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.client.screen.get_rect().right)

        if all(not validate_monster(mon) for mon in self.character.monsters):
            party_unselectable = T.translate("combat_party_unselectable")
            tools.open_dialog(self.client, [party_unselectable])

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""

        def choose_item() -> None:
            # open menu to choose item
            menu = self.client.push_state(ItemMenuState(self.character))

            # set next menu after the selection is made
            menu.is_valid_entry = validate_item  # type: ignore[method-assign]
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def choose_target(menu_item: MenuItem[Item]) -> None:
            # open menu to choose target of item
            item = menu_item.game_object
            self.client.remove_state_by_name("ItemMenuState")
            if State["MainCombatMenuState"] in item.usable_in:
                if item.behaviors.throwable:
                    enemy = self.opponents[0]
                    surface = Surface(self.rect.size)
                    mon = MenuItem(surface, None, None, enemy)
                    enqueue_item(item, mon)
                else:
                    state = self.client.push_state(
                        MonsterMenuState(self.character)
                    )
                    state.is_valid_entry = partial(validate, item)  # type: ignore[method-assign]
                    state.on_menu_selection = partial(enqueue_item, item)  # type: ignore[method-assign]

        def validate_item(item: Optional[Item]) -> bool:
            if item and item.behaviors.throwable:
                for opponent in self.opponents:
                    if not item.validate_monster(self.session, opponent):
                        return False
                return True
            return True

        def validate(item: Item, menu_item: MenuItem[Monster]) -> bool:
            if isinstance(menu_item, Monster):
                return item.validate_monster(self.session, menu_item)
            return False

        def enqueue_item(item: Item, menu_item: MenuItem[Monster]) -> None:
            target = menu_item.game_object

            # check target status
            if target.status:
                target.status[0].combat_state = self.combat
                target.status[0].phase = "enqueue_item"
                result_status = target.status[0].use(self.session, target)
                if result_status.extras:
                    templates = [
                        T.translate(extra) for extra in result_status.extras
                    ]
                    template = "\n".join(templates)
                    tools.open_dialog(self.client, [template])
                    return

            # enqueue the item
            self.combat.enqueue_action(self.character, item, target)

            # close all the open menus
            self.client.remove_state_by_name("MainCombatMenuState")
            if not item.behaviors.throwable:
                self.client.remove_state_by_name("MonsterMenuState")

        choose_item()

    def open_technique_menu(self) -> None:
        """Open menus to choose a Technique to use."""

        def choose_technique() -> None:
            available_techniques = [
                tech
                for tech in self.monster.moves
                if not combat.recharging(tech)
            ]

            # open menu to choose technique
            menu = self.client.push_state(Menu())
            menu.shrink_to_items = True

            if not available_techniques:
                skip = Technique.create("skip")
                skip_image = self.shadow_text(skip.name)
                tech_skip = MenuItem(skip_image, None, None, skip)
                menu.add(tech_skip)

            for tech in self.monster.moves:
                tech_name = tech.name
                tech_color = None
                tech_enabled = True

                if combat.recharging(tech):
                    tech_name = f"{tech.name} ({abs(tech.next_use)})"
                    tech_color = self.unavailable_color
                    tech_enabled = False

                tech_image = self.shadow_text(tech_name, fg=tech_color)
                item = MenuItem(tech_image, None, None, tech, tech_enabled)
                menu.add(item)

            # Update selected_index to the first enabled item
            enabled_items = [
                i for i, item in enumerate(menu.menu_items) if item.enabled
            ]
            if enabled_items:
                menu.selected_index = enabled_items[0]

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.client.screen.get_rect().right)

            # set next menu after the selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

            def show() -> None:
                tech = menu.get_selected_item()
                assert tech and tech.game_object
                types = " ".join(
                    map(lambda s: (s.name), tech.game_object.types)
                )
                label = T.format(
                    "technique_combat",
                    {
                        "name": tech.game_object.name,
                        "types": types,
                        "acc": int(tech.game_object.accuracy * 100),
                        "pow": tech.game_object.power,
                        "max_pow": prepare.POWER_RANGE[1],
                        "rec": str(tech.game_object.recharge_length),
                    },
                )
                self.combat.alert(label, dialog_speed="max")

            def hide() -> None:
                name = (
                    ""
                    if self.monster.owner is None
                    else self.monster.owner.name
                )
                params = {"name": self.monster.name, "player": name}
                message = T.format(self.combat.graphics.msgid, params)
                self.combat.alert(message, dialog_speed="max")

            menu.on_menu_selection_change_callback = show
            menu.on_close_callback = hide
            menu.on_menu_selection_change()
            menu.on_close()

        def choose_target(menu_item: MenuItem[Technique]) -> None:
            # open menu to choose target of technique
            technique = menu_item.game_object

            # allow to choose target if 1 vs 2 or 2 vs 2
            if len(self.opponents) > 1:
                state = self.client.push_state(
                    CombatTargetMenuState(
                        combat_state=self.combat,
                        monster=self.monster,
                        technique=technique,
                    )
                )
                state.on_menu_selection = partial(enqueue_technique, technique)  # type: ignore[method-assign]
            else:
                player = self.party[0]
                enemy = self.opponents[0]
                surface = Surface(self.rect.size)
                if technique.target["own_monster"]:
                    mon = MenuItem(surface, None, None, player)
                else:
                    mon = MenuItem(surface, None, None, enemy)
                enqueue_technique(technique, mon)

        def enqueue_technique(
            technique: Technique,
            menu_item: MenuItem[Monster],
        ) -> None:
            # enqueue the technique
            target = menu_item.game_object

            # Check if the technique can be used on the target
            if not technique.validate_monster(self.session, target):
                params = {"name": technique.name.upper()}
                msg = T.format("cannot_use_tech_monster", params)
                tools.open_dialog(self.client, [msg])
                return

            if (
                combat.has_effect(technique, "damage")
                and target == self.monster
            ):
                params = {"name": technique.name.upper()}
                msg = T.format("combat_target_itself", params)
                tools.open_dialog(self.client, [msg])
                return

            # Pre-check the technique for validity
            self.combat._combat_variables["action_tech"] = technique.slug
            technique = combat.pre_checking(
                self.session, self.monster, technique, target, self.combat
            )

            # Enqueue the action
            self.combat.enqueue_action(self.monster, technique, target)

            # close all the open menus
            if len(self.opponents) > 1:
                self.client.remove_state_by_name("CombatTargetMenuState")
            self.client.remove_state_by_name("Menu")
            self.client.remove_state_by_name("MainCombatMenuState")

        choose_technique()


class CombatTargetMenuState(Menu[Monster]):
    """Menu for selecting targets of techniques and items."""

    transparent = True

    def __init__(
        self, combat_state: CombatState, monster: Monster, technique: Technique
    ) -> None:
        super().__init__()
        assert monster.owner
        self.monster = monster
        self.combat_state = combat_state
        self.character = monster.owner
        self.technique = technique

        self.menu_items = VisualSpriteList(parent=self.calc_menu_items_rect)
        self.menu_sprites = SpriteGroup()
        self.targeting_map: defaultdict[str, list[Monster]] = defaultdict(list)

        self._create_menu()

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        """Generates menu items based on targeting rules."""
        if (
            self.technique.has_type("aether")
            or self.technique.sort == TechSort.meta
        ):
            yield self._create_menu_item(self.monster)
            return

        for player, monsters in self.combat_state.monsters_in_play.items():
            targeting_class = (
                "own_monster" if player == self.character else "enemy_monster"
            )
            self.targeting_map[targeting_class].extend(monsters)

            if (
                targeting_class not in self.technique.target
                or not self.technique.target[targeting_class]
            ):
                continue

            for monster in monsters:
                yield self._create_menu_item(monster)

    def _create_menu_item(self, monster: Monster) -> MenuItem[Monster]:
        """Creates a menu item for a given monster."""
        sprite = self.combat_state._monster_sprite_map[monster]
        item = MenuItem(self.surface, None, monster.name, monster)
        item.rect = sprite.rect.copy()
        item.rect.inflate_ip(tools.scale(1), tools.scale(1))
        return item

    def _create_menu(self) -> None:
        """Sets up the menu UI."""
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w // 2, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h

        self.window = GraphicBox(
            graphics.load_and_scale(self.borders_filename),
            None,
            self.background_color,
        )
        self.window.rect = rect
        self.sprites.add(self.window, layer=100)

        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.window.calc_inner_rect(self.window.rect)
        self.sprites.add(self.text_area, layer=100)

        self.surface = Surface(self.window.rect.size, SRCALPHA)
        self.border = GraphicBox(
            graphics.load_and_scale(self.borders_filename), None, None
        )

    def determine_target(self) -> None:
        """Finds the best target based on technique settings."""
        for target_tag, target_value in self.technique.target.items():
            if target_value:
                for target in self.targeting_map.get(target_tag, []):
                    menu_item = self.search_items(target)
                    if menu_item and menu_item.enabled:
                        self.selected_index = self.menu_items.sprites().index(
                            menu_item
                        )
                        return

    def refresh_layout(self) -> None:
        """Updates layout after determining the target."""
        self.determine_target()
        super().refresh_layout()

    def _update_borders(self) -> None:
        """Clears old borders and draws new ones around the selected item."""
        for sprite in self.menu_items:
            sprite.image.fill((0, 0, 0, 0))

        if selected := self.get_selected_item():
            selected.image = Surface(selected.rect.size, SRCALPHA)
            monster = selected.game_object
            pos = self.combat_state._monster_sprite_map[monster]
            scale = tools.scale(12)
            selected.rect.center = (
                pos.rect.centerx - scale,
                pos.rect.centery - scale,
            )
            self.border.draw(selected.image)

            if selected.description:
                self.alert(selected.description)

    def on_menu_selection_change(self) -> None:
        """Handles border updates when selection changes."""
        self.hide_cursor()
        self._update_borders()
