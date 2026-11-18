# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import scale as pg_scale

from tuxemon.graphics import load_and_scale, load_image
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster.monster import Monster
from tuxemon.sprite import Sprite
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.states.combat_state import CombatState
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], None]


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

        self._crosshairs_sprite: Sprite | None = None

        self._create_menu()

    def _build_targeting_map(self) -> None:
        """Group active monsters into own-side and enemy-side targets."""
        self.targeting_map.clear()

        for (
            player,
            monsters,
        ) in self.combat_session.field_monsters.get_all_monsters().items():
            target_group = (
                "own_monster" if player == self.character else "enemy_monster"
            )

            self.targeting_map[target_group].extend(monsters)

    def _can_target_group(self, target_group: str) -> bool:
        """Return whether the technique can target the given group."""
        show = self.technique.target.get(target_group)

        if not show and target_group == "enemy_monster":
            show = self.technique.targets_enemy()

        return bool(show)

    def _iter_bypass_targets(self) -> Generator[Monster, None, None]:
        """Yield the automatic target when the technique bypasses selection."""
        if self.technique.target.get("enemy_monster"):
            for (
                player,
                monsters,
            ) in self.combat_session.field_monsters.get_all_monsters().items():
                if player != self.character and monsters:
                    yield monsters[0]
                    return
        else:
            yield self.monster

    def _iter_target_monsters(self) -> Generator[Monster, None, None]:
        """Yield monsters in groups allowed by the technique's targeting rules."""
        for (
            target_group,
            monsters,
        ) in self.targeting_map.items():
            if not self._can_target_group(target_group):
                continue

            yield from monsters

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        """Generate menu items from valid combat targets."""

        if self.technique.behaviors.bypasses_selection:
            targets = self._iter_bypass_targets()
        else:
            self._build_targeting_map()
            targets = self._iter_target_monsters()

        for monster in targets:
            yield self._create_menu_item(monster)

    def _create_menu_item(self, monster: Monster) -> MenuItem[Monster]:
        sprite = self.combat.sprite_map.get_sprite(monster)

        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")

        item = MenuItem(
            self.surface,
            None,
            monster.name,
            monster,
        )

        item.rect = sprite.rect.copy()
        item.rect.inflate_ip(self.factor, self.factor)

        return item

    def _create_menu(self) -> None:
        rect_screen = self.client.context.rect.copy()

        rect = Rect(
            0,
            0,
            rect_screen.w // 2,
            rect_screen.h // 4,
        )

        rect.bottomright = (
            rect_screen.w,
            rect_screen.h,
        )

        self.window = GraphicBox(
            rect,
            load_and_scale(self.borders_filename),
            color=self.background_color,
        )

        self.sprites.add(
            self.window,
            layer=100,
        )

        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=self.window.inner_rect,
            scaling=self.client.context.scaling,
        )

        self.sprites.add(
            self.text_area,
            layer=100,
        )

        self.surface = Surface(
            self.window.rect.size,
            SRCALPHA,
        )

        self.border = GraphicBox(
            Rect(0, 0, 1, 1),
            load_and_scale(self.borders_filename),
        )

    def _find_default_target(self) -> MenuItem[Monster] | None:
        """Find the first enabled menu item matching the technique's targets."""
        for target_tag, enabled in self.technique.target.items():
            if not enabled:
                continue

            for target in self.targeting_map.get(target_tag, []):
                item = self.search_items(target)
                if item and item.enabled:
                    return item

        if self._can_target_group("enemy_monster"):
            for target in self.targeting_map.get("enemy_monster", []):
                item = self.search_items(target)
                if item and item.enabled:
                    return item

        return None

    def determine_target(self) -> None:
        """Select the first enabled item matching the technique's target rules."""
        item = self._find_default_target()

        if item is None:
            return

        self.selected_index = self.menu_items.sprites().index(item)

    def refresh_layout(
        self,
        *,
        mutate: bool = True,
    ) -> Rect:
        self.determine_target()
        return super().refresh_layout(mutate=mutate)

    def _update_borders(self) -> None:
        for sprite in self.menu_items:
            sprite.image.fill((0, 0, 0, 0))

        if self._crosshairs_sprite is not None:
            self._crosshairs_sprite.kill()
            self._crosshairs_sprite = None

        if selected := self.get_selected_item():
            monster = selected.game_object

            pos = self.combat.sprite_map.get_sprite(monster)

            if pos is None:
                return

            s = self.client.context.scaling.scale_int(64)

            crosshairs_image = pg_scale(
                load_image("gfx/ui/combat/crosshairs.png"),
                (s, s),
            )

            spr = Sprite()
            spr.image = crosshairs_image

            spr.rect = crosshairs_image.get_rect(center=pos.rect.center)

            self.sprites.add(
                spr,
                layer=101,
            )

            self._crosshairs_sprite = spr

            if selected.description:
                self.dialog.alert(
                    selected.description,
                    self.text_area,
                )

    def update_cursor_visibility(self) -> None:
        self.hide_cursor()

    def on_open(self) -> None:
        items = [item for item in self.menu_items if item.enabled]

        if len(items) == 1:
            self.on_menu_selection(items[0])

    def on_menu_selection_change(self) -> None:
        self.hide_cursor()
        self._update_borders()

    def on_menu_selection(self, item: MenuItem[Monster]) -> None:
        if self._external_on_selection:
            return self._external_on_selection(item)

    def is_valid_entry(self, monster: Monster | None) -> bool:
        if self._external_is_valid_entry:
            return self._external_is_valid_entry(monster)

        return monster is not None
