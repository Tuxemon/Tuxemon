# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Optional

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import graphics, prepare, tools
from tuxemon.combat import utils
from tuxemon.combat.menu_visibility import MenuProfiles
from tuxemon.db import EffectPhase, State, TechSort
from tuxemon.item.filter import ItemFilter
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.monster import Monster
from tuxemon.sprite import Sprite
from tuxemon.states.item_menu import ItemMenuState
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.tools import fix_measure
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session
    from tuxemon.states.combat_state import CombatState

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], None]


class MainCombatMenuState(PopUpMenu[MenuGameObj]):
    """
    Main menu for combat: Fight, Item, Swap, Run

    TODO: there needs to be more general use registers in the combat state to
    query what player is doing what. There's lots of spaghetti right now.
    """

    name: ClassVar[str] = "MainCombatMenuState"
    escape_key_exits = False
    columns = 2

    def __init__(
        self, session: Session, cmb: CombatState, monster: Monster
    ) -> None:
        super().__init__()
        self.rect = self.calculate_menu_rectangle()
        self.session = session
        self.combat_session = self.client.combat_session
        self.combat = cmb
        self.character = monster.get_owner()
        self.monster = monster
        self.party = self.combat_session.field_monsters.get_monsters(
            self.character
        )
        if self.character == self.combat_session.left_player:
            self.enemy = self.combat_session.right_player
            self.opponents = self.combat_session.field_monsters.get_monsters(
                self.enemy
            )
        if self.character == self.combat_session.right_player:
            self.enemy = self.combat_session.left_player
            self.opponents = self.combat_session.field_monsters.get_monsters(
                self.enemy
            )
        params = {"name": monster.name}
        message = T.format("combat_monster_choice", params)
        self.combat.dialog.alert(message)

        self.type_icon_sprites: list[Sprite] = []
        self.text_sprites: dict[str, Sprite] = {}
        self.range_icon_sprite: Optional[Sprite] = None
        self.speed_icon_sprite: Optional[Sprite] = None

    def _clear_tech_overlay(self) -> None:
        """Remove technique icons/text from the overlay."""
        if hasattr(self, "range_icon_sprite") and self.range_icon_sprite:
            if self.range_icon_sprite in self.sprites:
                self.sprites.remove(self.range_icon_sprite)
            self.range_icon_sprite = None

        if hasattr(self, "speed_icon_sprite") and self.speed_icon_sprite:
            if self.speed_icon_sprite in self.sprites:
                self.sprites.remove(self.speed_icon_sprite)
            self.speed_icon_sprite = None

        if hasattr(self, "type_icon_sprites"):
            for spr in self.type_icon_sprites:
                if spr in self.sprites:
                    self.sprites.remove(spr)

        if hasattr(self, "text_sprites"):
            for spr in self.text_sprites.values():
                if spr in self.sprites:
                    self.sprites.remove(spr)

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = prepare.SCREEN_RECT.copy()
        menu_width = fix_measure(rect_screen.w, 102 / 256)
        menu_height = fix_measure(rect_screen.h, 36 / 144)
        rect = Rect(0, 0, menu_width, menu_height)
        rect.bottomright = rect_screen.w, rect_screen.h
        return rect

    def get_menu_profile(self) -> tuple[dict[str, str], dict[str, bool]]:
        if self.combat_session.is_trainer_battle:
            return MenuProfiles.default_trainer_battle()
        else:
            return MenuProfiles.default_monster_battle()

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        menu_map, default_visibility = self.get_menu_profile()

        visibility_map = default_visibility.copy()

        visibility_map.update(self.combat_session.menu_visibility_map)

        for key, method_name in menu_map.items():
            callback = getattr(self, method_name)
            visible = visibility_map.get(key, False)
            foreground = self.unavailable_color if not visible else None

            yield MenuItem(
                self.shadow_text(T.translate(key).upper(), fg=foreground),
                T.translate(key).upper(),
                None,
                callback,
                visible,
            )

    def forfeit(self) -> None:
        """
        Cause player to forfeit from the trainer battles.
        """
        forfeit = Technique.create("menu_forfeit")
        self.client.remove_state_by_name("MainCombatMenuState")
        self.combat_session.enqueue_action(
            self.party[0], forfeit, self.opponents[0]
        )

    def run(self) -> None:
        """
        Cause player to run from the wild encounters.
        """
        run = Technique.create("menu_run")
        status = self.monster.status.get_current_status()
        message = status.name.lower() if status else ""
        if not run.validate_monster(self.session, self.monster):
            params = {
                "monster": self.monster.name.upper(),
                "status": message,
            }
            msg = T.format("combat_player_run_status", params)
            tools.open_dialog(self.client, [msg])
            return
        self.client.remove_state_by_name("MainCombatMenuState")
        self.combat_session.enqueue_action(
            self.party[0], run, self.opponents[0]
        )

    def open_swap_menu(self) -> None:
        """Open menus to swap monsters in party."""

        def swap_it(menuitem: MenuItem[Monster]) -> None:
            added = menuitem.game_object
            swap = Technique.create("swap")
            status = self.monster.status.get_current_status()
            message = status.name.lower() if status else ""
            if not swap.validate_monster(self.session, self.monster):
                params = {
                    "monster": self.monster.name.upper(),
                    "status": message,
                }
                msg = T.format("combat_player_swap_status", params)
                tools.open_dialog(self.client, [msg])
                return
            self.combat_session.swap_tracker.register(added)
            self.combat_session.enqueue_action(self.monster, swap, added)
            self.client.remove_state_by_name("MonsterMenuState")
            self.client.remove_state_by_name("MainCombatMenuState")

        def validate_monster(menu_item: Monster) -> bool:
            if menu_item.is_fainted:
                return False
            if menu_item in self.combat_session.active_monsters:
                return False
            if not self.combat_session.swap_tracker.can_swap(menu_item):
                return False
            return True

        def validate(menu_item: MenuItem[Monster]) -> bool:
            if isinstance(menu_item, Monster):
                return validate_monster(menu_item)
            return False

        menu = self.client.push_state(
            MonsterMenuState(self.character.monsters)
        )
        menu.on_menu_selection = swap_it  # type: ignore[assignment]
        menu.is_valid_entry = validate  # type: ignore[assignment]
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", prepare.SCREEN_RECT.right)

        if all(not validate_monster(mon) for mon in self.character.monsters):
            party_unselectable = T.translate("combat_party_unselectable")
            tools.open_dialog(self.client, [party_unselectable])

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""

        def choose_item() -> None:
            # open menu to choose item
            items_filtered = ItemFilter(self.character)
            items_filtered.set_filter_usable_in_state("MainCombatMenuState")
            menu = self.client.push_state(
                ItemMenuState(self.character, self.name, items_filtered)
            )

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
                        MonsterMenuState(self.character.monsters)
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
            status = target.status.get_current_status()
            if status:
                result_status = status.use(
                    self.session, target, EffectPhase.ENQUEUE_ITEM
                )
                if result_status.extras:
                    templates = [
                        T.translate(extra) for extra in result_status.extras
                    ]
                    template = "\n".join(templates)
                    tools.open_dialog(self.client, [template])
                    return

            # enqueue the item
            self.combat_session.enqueue_action(self.character, item, target)

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
                for tech in self.monster.moves.get_moves()
                if not tech.is_recharging
            ]

            # open menu to choose technique
            menu = self.client.push_state(Menu())
            menu.shrink_to_items = True

            if not available_techniques:
                skip = Technique.create("skip")
                skip_image = self.shadow_text(skip.name)
                tech_skip = MenuItem(skip_image, None, None, skip)
                menu.add(tech_skip)

            for tech in self.monster.moves.get_moves():
                tech_name = tech.name
                tech_color = None
                tech_enabled = True

                if tech.is_recharging:
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
            menu.anchor("right", prepare.SCREEN_RECT.right)

            # set next menu after the selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

            def show() -> None:
                # Clear the combat dialog so the old "What will X do?" text disappears
                self.combat.dialog.alert("", dialog_speed="max")

                screen_w, screen_h = prepare.SCREEN_SIZE

                # --- Clear old sprites if they exist ---
                if (
                    hasattr(self, "range_icon_sprite")
                    and self.range_icon_sprite
                ):
                    if self.range_icon_sprite in self.sprites:
                        self.sprites.remove(self.range_icon_sprite)
                    self.range_icon_sprite = None

                if (
                    hasattr(self, "speed_icon_sprite")
                    and self.speed_icon_sprite
                ):
                    if self.speed_icon_sprite in self.sprites:
                        self.sprites.remove(self.speed_icon_sprite)
                    self.speed_icon_sprite = None

                if hasattr(self, "type_icon_sprites"):
                    for spr in self.type_icon_sprites:
                        if spr in self.sprites:
                            self.sprites.remove(spr)
                self.type_icon_sprites = []

                if hasattr(self, "text_sprites"):
                    for spr in self.text_sprites.values():
                        if spr in self.sprites:
                            self.sprites.remove(spr)
                self.text_sprites = {}

                # --- Technique reference ---
                tech = menu.get_selected_item()
                assert tech and tech.game_object
                technique = tech.game_object

                # --- Draw type icons ---
                if technique.types.current:
                    for i, t in enumerate(technique.types.current[:2]):
                        path = f"gfx/ui/icons/element/{t.name.lower()}_type_small.png"
                        try:
                            icon_surface = graphics.load_and_scale(
                                path, prepare.SCALE
                            )
                            spr = Sprite()
                            spr.image = icon_surface
                            spr.rect = spr.image.get_rect()

                            # Position independently on grid
                            if i == 0:
                                spr.rect.topleft = (
                                    fix_measure(screen_w, 136 / 256),
                                    fix_measure(screen_h, 126 / 144),
                                )
                            else:
                                spr.rect.topleft = (
                                    fix_measure(screen_w, 144 / 256),
                                    fix_measure(screen_h, 126 / 144),
                                )

                            self.sprites.add(spr, layer=200)
                            self.type_icon_sprites.append(spr)
                        except Exception as e:
                            print(f"Could not load type icon {path}: {e}")

                # --- Draw range icon ---
                if technique.range:
                    path = f"gfx/ui/icons/range/{technique.range.name.lower()}.png"
                    try:
                        surf = graphics.load_and_scale(path, prepare.SCALE)
                        spr = Sprite()
                        spr.image = surf
                        spr.rect = surf.get_rect()
                        spr.rect.topleft = (
                            fix_measure(screen_w, 7 / 256),
                            fix_measure(screen_h, 121 / 144),
                        )
                        self.sprites.add(spr, layer=200)
                        self.range_icon_sprite = spr
                    except Exception as e:
                        print(f"Could not load range icon {path}: {e}")

                # --- Draw speed icon ---
                if technique.speed is not None:
                    mapping = {
                        -3: "extremely_slow",
                        -2: "very_slow",
                        -1: "slow",
                        0: "normal",
                        1: "fast",
                        2: "very_fast",
                        3: "extremely_fast",
                    }
                    if hasattr(technique.speed, "value"):
                        speed_val = technique.speed.value
                    elif isinstance(technique.speed, int):
                        speed_val = mapping.get(technique.speed, "normal")
                    else:
                        speed_val = str(technique.speed).lower()

                    path = f"gfx/ui/icons/speed/{speed_val}.png"
                    try:
                        surf = graphics.load_and_scale(path, prepare.SCALE)
                        spr = Sprite()
                        spr.image = surf
                        spr.rect = surf.get_rect()
                        spr.rect.topleft = (
                            fix_measure(screen_w, 135 / 256),
                            fix_measure(screen_h, 113 / 144),
                        )
                        self.sprites.add(spr, layer=200)
                        self.speed_icon_sprite = spr
                    except Exception as e:
                        print(f"Could not load speed icon {path}: {e}")

                # --- Draw text labels ---
                font = self.font
                scaled_pow = int(technique.power * (7 + self.monster.level))

                text_lines = {
                    "accuracy": f"{T.translate('technique_accuracy')} {int(technique.accuracy * 100)}%",
                    "recharge": f"{T.translate('technique_recharge')} {technique.recharge_length} {T.translate('technique_turns')}",
                }

                # Only add Power if it's not zero
                if scaled_pow > 0:
                    text_lines["power"] = (
                        f"{T.translate('technique_power')} {scaled_pow}"
                    )

                for key, line in text_lines.items():
                    surf = font.render(line, True, (0, 0, 0))  # black text
                    spr = Sprite()
                    spr.image = surf
                    spr.rect = surf.get_rect()

                    # Independent positioning (you can tweak these individually)
                    if key == "accuracy":
                        spr.rect.topleft = (
                            fix_measure(screen_w, 7 / 256),
                            fix_measure(screen_h, 114 / 144),
                        )
                    elif key == "power":
                        spr.rect.topleft = (
                            fix_measure(screen_w, 44 / 256),
                            fix_measure(screen_h, 123 / 144),
                        )
                    elif key == "recharge":
                        spr.rect.topleft = (
                            fix_measure(screen_w, 7 / 256),
                            fix_measure(screen_h, 133 / 144),
                        )

                    self.sprites.add(spr, layer=200)
                    self.text_sprites[key] = spr

            def hide() -> None:
                # Clear all technique overlay sprites
                self._clear_tech_overlay()

                # Restore the original combat prompt
                params = {"name": self.monster.name}
                message = T.format("combat_monster_choice", params)
                self.combat.dialog.alert(message, dialog_speed="max")

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
                utils.has_effect(technique, "damage")
                and target == self.monster
            ):
                params = {"name": technique.name.upper()}
                msg = T.format("combat_target_itself", params)
                tools.open_dialog(self.client, [msg])
                return

            # Pre-check the technique for validity
            self.combat_session.set_variable("action_tech", technique.slug)
            technique = self.combat_session.pre_checking(
                self.session, self.monster, technique, target
            )

            # Enqueue the action
            self.combat_session.enqueue_action(self.monster, technique, target)

            # close all the open menus
            if len(self.opponents) > 1:
                self.client.remove_state_by_name("CombatTargetMenuState")
            self.client.remove_state_by_name("Menu")
            self.client.remove_state_by_name("MainCombatMenuState")

        choose_technique()


class CombatTargetMenuState(Menu[Monster]):
    """Menu for selecting targets of techniques and items."""

    name: ClassVar[str] = "CombatTargetMenuState"
    transparent = True

    def __init__(
        self, combat_state: CombatState, monster: Monster, technique: Technique
    ) -> None:
        super().__init__()
        self.monster = monster
        self.combat_state = combat_state
        self.combat_session = self.client.combat_session
        self.character = monster.get_owner()
        self.technique = technique
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

        for (
            player,
            monsters,
        ) in self.combat_session.field_monsters.get_all_monsters().items():
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
        sprite = self.combat_state.sprite_map.get_sprite(monster)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")
        item = MenuItem(self.surface, None, monster.name, monster)
        item.rect = sprite.rect.copy()
        item.rect.inflate_ip(tools.scale(1), tools.scale(1))
        return item

    def _create_menu(self) -> None:
        """Sets up the menu UI."""
        rect_screen = prepare.SCREEN_RECT.copy()
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
            pos = self.combat_state.sprite_map.get_sprite(monster)
            if pos is None:
                raise KeyError(f"Sprite not found for entity: {monster.name}")
            scale = tools.scale(12)
            selected.rect.center = (
                pos.rect.centerx - scale,
                pos.rect.centery - scale,
            )
            self.border.draw(selected.image)

            if selected.description:
                self.dialog.alert(selected.description)

    def on_menu_selection_change(self) -> None:
        """Handles border updates when selection changes."""
        self.hide_cursor()
        self._update_borders()
