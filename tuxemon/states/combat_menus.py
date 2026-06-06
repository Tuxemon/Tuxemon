# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.combat.menu_visibility import MenuProfiles
from tuxemon.db import EffectPhase, SpeedLabel, State
from tuxemon.graphics import load_and_scale
from tuxemon.item.filter import ItemFilter
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.monster.monster import Monster
from tuxemon.sprite import Sprite
from tuxemon.states.item_menu import ItemMenuState
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.tools import fix_measure, open_dialog
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
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
        self,
        client: BaseClient,
        session: Session,
        combat: CombatState,
        character: NPC,
        monster: Monster,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)
        self.rect = self.calculate_menu_rectangle()
        self.session = session
        self.combat_session = self.client.combat_session
        self.combat = combat
        self.character = character
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
        self.event_bus.publish("combat_dialog", message=message)

        self.type_icon_sprites: list[Sprite] = []
        self.text_sprites: dict[str, Sprite] = {}
        self.range_icon_sprite: Sprite | None = None
        self.speed_icon_sprite: Sprite | None = None

    def _clear_tech_overlay(self) -> None:
        """Remove technique icons/text from the overlay."""
        if self.range_icon_sprite:
            if self.range_icon_sprite in self.sprites:
                self.sprites.remove(self.range_icon_sprite)
            self.range_icon_sprite = None

        if self.speed_icon_sprite:
            if self.speed_icon_sprite in self.sprites:
                self.sprites.remove(self.speed_icon_sprite)
            self.speed_icon_sprite = None

        if self.type_icon_sprites:
            for spr in self.type_icon_sprites:
                if spr in self.sprites:
                    self.sprites.remove(spr)

        if self.text_sprites:
            for spr in self.text_sprites.values():
                if spr in self.sprites:
                    self.sprites.remove(spr)

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = self.client.context.rect.copy()
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

        if self.enemy.combat.forfeit:
            visibility_map["menu_forfeit"] = True

        # Hide Item if no usable items
        items_filtered = ItemFilter(self.character.items)
        items_filtered.set_filter_combat_targets(
            self.session, self.character.monsters, self.opponents
        )
        if not items_filtered.items:
            visibility_map["menu_item"] = False

        # Hide Swap if no valid swap targets
        if not self.can_swap_any(self.character):
            visibility_map["menu_monster"] = False

        # Yield menu items
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
        status = self.monster.status.current_status
        message = status.name.lower() if status else ""
        if not run.validate_monster(self.session, self.monster):
            params = {
                "monster": self.monster.name.upper(),
                "status": message,
            }
            msg = T.format("combat_player_run_status", params)
            open_dialog(self.client, [msg], dialog_speed="max")
            return
        self.client.remove_state_by_name("MainCombatMenuState")
        self.combat_session.enqueue_action(
            self.party[0], run, self.opponents[0]
        )

    def can_swap_any(self, character: NPC) -> bool:
        """Return True if the character has at least one valid swap target."""
        active = self.combat_session.active_monsters
        tracker = self.combat_session.swap_tracker

        # If all monsters are active, no swap is possible
        if len(character.monsters) <= len(active):
            return False

        for mon in character.monsters:
            if mon.is_fainted:
                continue
            if mon in active:
                continue
            if not tracker.can_swap(mon):
                continue
            return True

        return False

    def open_swap_menu(self) -> None:
        """Open menus to swap monsters in party."""

        def swap_it(menuitem: MenuItem[Monster | None]) -> None:
            added = menuitem.game_object

            if added is None:
                return

            swap = Technique.create("swap")
            status = self.monster.status.current_status
            message = status.name.lower() if status else ""

            if not swap.validate_monster(self.session, self.monster):
                params = {
                    "monster": self.monster.name.upper(),
                    "status": message,
                }
                msg = T.format("combat_player_swap_status", params)
                open_dialog(self.client, [msg], dialog_speed="max")
                return

            self.combat_session.swap_tracker.register(added)
            self.combat_session.enqueue_action(self.monster, swap, added)
            self.client.pop_state()
            self.client.pop_state()

        def validate_monster(mon: Monster) -> bool:
            if mon.is_fainted:
                return False
            if mon in self.combat_session.active_monsters:
                return False
            if not self.combat_session.swap_tracker.can_swap(mon):
                return False
            return True

        def validate(mon: Monster | None) -> bool:
            if mon is None:
                return False
            return validate_monster(mon)

        menu = self.client.push_state(
            MonsterMenuState(
                self.client,
                self.character.monsters,
                on_selection=swap_it,
                is_valid_entry=validate,
            )
        )
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.client.context.rect.right)

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""

        def choose_item() -> None:
            # open menu to choose item
            items_filtered = ItemFilter(self.character.items)
            items_filtered.set_filter_combat_targets(
                self.session, self.character.monsters, self.opponents
            )
            self.client.push_state(
                ItemMenuState(
                    self.client,
                    character=self.character,
                    source=self.name,
                    item_filter=items_filtered,
                    on_selection=choose_target,
                    is_valid_entry=validate_item,
                )
            )

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
                    self.client.push_state(
                        MonsterMenuState(
                            self.client,
                            self.character.monsters,
                            on_selection=partial(enqueue_item, item),
                            is_valid_entry=partial(validate, item),
                        )
                    )

        def validate_item(item: Item | None) -> bool:
            if item and item.behaviors.throwable:
                for opponent in self.opponents:
                    if not item.validate_monster(self.session, opponent):
                        return False
                return True
            return True

        def validate(item: Item, monster: Monster | None) -> bool:
            if monster is None:
                return False
            return item.validate_monster(self.session, monster)

        def enqueue_item(
            item: Item, menu_item: MenuItem[Monster | None]
        ) -> None:
            target = menu_item.game_object
            if target is None:
                return

            # check target status
            status = target.status.current_status
            if status:
                result_status = status.use(
                    self.session, EffectPhase.ENQUEUE_ITEM
                )
                if result_status.extras:
                    templates = [
                        T.translate(extra) for extra in result_status.extras
                    ]
                    template = "\n".join(templates)
                    open_dialog(self.client, [template], dialog_speed="max")
                    return

            # enqueue the item
            self.combat_session.enqueue_action(self.character, item, target)
            self.character.battle_last_used_item_slug = item.slug

            # close all the open menus
            self.client.remove_state_by_name("MainCombatMenuState")
            if not item.behaviors.throwable:
                self.client.remove_state_by_name("MonsterMenuState")

        choose_item()

    def open_technique_menu(self) -> None:
        """Open menus to choose a Technique to use."""

        def choose_technique() -> None:
            usable_moves = self.monster.moves.get_usable_moves(
                self.session, self.opponents
            )

            menu: Menu[Any] = self.client.push_state(Menu(self.client))
            menu.shrink_to_items = True

            # No usable moves → show only fallback/skip
            if not usable_moves:
                fallback_moves = self.monster.moves.get_fallback_moves()
                for fb in fallback_moves:
                    menu.add(
                        MenuItem(self.shadow_text(fb.name), None, None, fb)
                    )

            # Normal case → show all moves with enabled/disabled state
            else:
                for tech in self.monster.moves.get_moves():
                    usable = any(
                        tech.can_use(self.session, opponent)
                        for opponent in self.opponents
                    )

                    if not usable:
                        if tech.is_recharging:
                            tech_name = (
                                f"{tech.name} ({tech.cooldown.remaining})"
                            )
                        else:
                            tech_name = tech.name
                        tech_color = self.unavailable_color
                        tech_enabled = False
                    else:
                        tech_name = tech.name
                        tech_color = None
                        tech_enabled = True

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
            menu.anchor("right", self.client.context.rect.right)

            # set next menu after the selection is made
            menu.on_selection_callback = choose_target

            def show() -> None:
                # Clear the combat dialog so the old "What will X do?" text disappears
                self.event_bus.publish(
                    "combat_dialog", message="", dialog_speed="max"
                )

                screen_w, screen_h = self.client.context.resolution

                # --- Clear old sprites if they exist ---
                if self.range_icon_sprite:
                    if self.range_icon_sprite in self.sprites:
                        self.sprites.remove(self.range_icon_sprite)
                    self.range_icon_sprite = None

                if self.speed_icon_sprite:
                    if self.speed_icon_sprite in self.sprites:
                        self.sprites.remove(self.speed_icon_sprite)
                    self.speed_icon_sprite = None

                if self.type_icon_sprites:
                    for spr in self.type_icon_sprites:
                        if spr in self.sprites:
                            self.sprites.remove(spr)
                self.type_icon_sprites = []

                if self.text_sprites:
                    for spr in self.text_sprites.values():
                        if spr in self.sprites:
                            self.sprites.remove(spr)
                self.text_sprites = {}

                # --- Technique reference ---
                tech = menu.get_selected_item()
                assert tech
                technique: Technique = tech.game_object

                # --- Draw type icons ---
                if technique.types.current:
                    for i, t in enumerate(technique.types.current[:2]):
                        path = f"gfx/ui/icons/element/{t.name.lower()}_type_small.png"
                        try:
                            icon_surface = load_and_scale(path, self.factor)
                            spr = Sprite()
                            spr.image = icon_surface
                            spr.rect = spr.image.get_rect()

                            # Position independently on grid
                            if i == 0:
                                spr.rect.topleft = (
                                    fix_measure(screen_w, 132 / 256),
                                    fix_measure(screen_h, 126 / 144),
                                )
                            else:
                                spr.rect.topleft = (
                                    fix_measure(screen_w, 142 / 256),
                                    fix_measure(screen_h, 126 / 144),
                                )

                            self.sprites.add(spr, layer=200)
                            self.type_icon_sprites.append(spr)
                        except Exception as e:
                            logger.error(
                                f"Could not load type icon {path}: {e}"
                            )

                # --- Draw range icon ---
                path = f"gfx/ui/icons/range/{technique.range.name.lower()}.png"
                try:
                    surf = load_and_scale(path, self.factor)
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
                    logger.error(f"Could not load range icon {path}: {e}")

                # --- Draw speed icon ---
                speed_label = SpeedLabel.from_numeric(technique.speed)
                speed_val = speed_label.value

                path = f"gfx/ui/icons/speed/{speed_val}.png"
                try:
                    surf = load_and_scale(path, self.factor)
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
                    logger.error(f"Could not load speed icon {path}: {e}")

                # --- Draw text labels ---
                font = self.font
                scaled_pow = int(technique.power * (7 + self.monster.level))

                text_lines = {
                    "accuracy": f"{T.translate('technique_accuracy')} {int(technique.accuracy * 100)}%",
                    "recharge": f"{T.translate('technique_recharge')} {technique.cooldown.duration} {T.translate('technique_turns')}",
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
                self.event_bus.publish(
                    "combat_dialog", message=message, dialog_speed="max"
                )

            menu.on_menu_selection_change_callback = show
            menu.on_close_callback = hide
            menu.on_menu_selection_change()
            menu.on_close()

        def choose_target(menu_item: MenuItem[Technique]) -> None:
            # open menu to choose target of technique
            technique = menu_item.game_object

            # allow to choose target if 1 vs 2 or 2 vs 2
            if len(self.opponents) > 1:
                self.client.push_state(
                    CombatTargetMenuState(
                        client=self.client,
                        combat=self.combat,
                        character=self.character,
                        monster=self.monster,
                        technique=technique,
                        on_selection=partial(enqueue_technique, technique),
                    )
                )
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
                open_dialog(self.client, [msg], dialog_speed="max")
                return

            if technique.has_effect("damage") and target == self.monster:
                params = {"name": technique.name.upper()}
                msg = T.format("combat_target_itself", params)
                open_dialog(self.client, [msg], dialog_speed="max")
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
            self.client.pop_state(self)

        choose_technique()


class CombatTargetMenuState(Menu[Monster]):
    """Menu for selecting targets of techniques and items."""

    name: ClassVar[str] = "CombatTargetMenuState"
    transparent = True

    def __init__(
        self,
        client: BaseClient,
        combat: CombatState,
        character: NPC,
        monster: Monster,
        technique: Technique,
        *,
        on_selection: Callable[[MenuItem[Monster]], None] | None = None,
        is_valid_entry: Callable[[Monster | None], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)
        self.character = character
        self.monster = monster
        self.combat = combat
        self.combat_session = self.client.combat_session
        self.technique = technique
        self._external_on_selection = on_selection
        self._external_is_valid_entry = is_valid_entry
        self.targeting_map: defaultdict[str, list[Monster]] = defaultdict(list)

        self._create_menu()

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        """Generates menu items based on targeting rules for 2vs2 or 1vs2 combat."""
        self.targeting_map.clear()

        if self.technique.behaviors.bypasses_selection:
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

            if not self.technique.target.get(targeting_class):
                continue

            for monster in monsters:
                yield self._create_menu_item(monster)

    def _create_menu_item(self, monster: Monster) -> MenuItem[Monster]:
        """Creates a menu item for a given monster."""
        sprite = self.combat.sprite_map.get_sprite(monster)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")
        item = MenuItem(self.surface, None, monster.name, monster)
        item.rect = sprite.rect.copy()
        item.rect.inflate_ip(self.factor, self.factor)
        return item

    def _create_menu(self) -> None:
        """Sets up the menu UI."""
        rect_screen = self.client.context.rect.copy()
        rect = Rect(0, 0, rect_screen.w // 2, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h

        self.window = GraphicBox(
            rect,
            load_and_scale(self.borders_filename),
            color=self.background_color,
        )
        self.sprites.add(self.window, layer=100)

        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=self.window.inner_rect,
            scaling=self.client.context.scaling,
        )
        self.sprites.add(self.text_area, layer=100)

        self.surface = Surface(self.window.rect.size, SRCALPHA)
        self.border = GraphicBox(
            Rect(0, 0, 1, 1),
            load_and_scale(self.borders_filename),
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

    def refresh_layout(self, *, mutate: bool = True) -> Rect:
        """Updates layout after determining the target."""
        self.determine_target()
        return super().refresh_layout(mutate=mutate)

    def _update_borders(self) -> None:
        """Draws borders around the currently selected monster in 2vs2/1vs2 combat."""
        for sprite in self.menu_items:
            sprite.image.fill((0, 0, 0, 0))

        if selected := self.get_selected_item():
            monster = selected.game_object
            pos = self.combat.sprite_map.get_sprite(monster)
            if pos is None:
                return

            selected.image = Surface(selected.rect.size, SRCALPHA)
            BORDER_OFFSET = self.client.context.scaling.scale_int(12)
            selected.rect.center = (
                pos.rect.centerx - BORDER_OFFSET,
                pos.rect.centery - BORDER_OFFSET,
            )
            self.border.draw(selected.image)

            if selected.description:
                self.dialog.alert(selected.description, self.text_area)

    def on_menu_selection_change(self) -> None:
        """Handles border updates when selection changes."""
        self.hide_cursor()
        self._update_borders()

    def on_menu_selection(self, item: MenuItem[Monster]) -> None:
        if self._external_on_selection:
            return self._external_on_selection(item)

    def is_valid_entry(self, monster: Monster | None) -> bool:
        if self._external_is_valid_entry:
            return self._external_is_valid_entry(monster)
        return monster is not None
