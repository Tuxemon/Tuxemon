# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon.animation import Animation
from tuxemon.sprite import Sprite
from tuxemon.state.state import State

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.ui.combat_hud import CombatLayoutManager


class StatusIconManager:
    """Handles creation, caching, and updating of status icons."""

    def __init__(
        self,
        state: State,
        layouts: dict[NPC, dict[str, list[Rect]]],
        position_tracker: CombatLayoutManager,
        layer: int = 200,
    ) -> None:
        self._state = state
        self._layouts = layouts
        self._tracker = position_tracker
        self._layer = layer
        self._status_icon_cache: dict[
            tuple[str, tuple[float, float]], Sprite
        ] = {}

    def create_icon_cache(self, active_monsters: Sequence[Monster]) -> None:
        for monster in active_monsters:
            ui = self._tracker._monster_ui.get(monster)
            if not ui:
                logger.warning(f"No UI found for monster '{monster}'")
                continue

            index = ui.slot_index
            ui.status_icons = []

            for status in monster.status.get_statuses():
                if status.icon:
                    position = self.get_icon_position(monster, index)
                    key = (status.icon, position)

                    if key not in self._status_icon_cache:
                        logger.debug(
                            f"Loading new icon '{status.icon}' at {position}"
                        )
                        sprite = self._state.load_sprite(
                            status.icon,
                            layer=self._layer,
                            center=position,
                        )
                        self._status_icon_cache[key] = sprite
                    else:
                        logger.debug(
                            f"Using cached icon '{status.icon}' at {position}"
                        )

                    ui.status_icons.append(self._status_icon_cache[key])

    def update_icons_for_monsters(
        self, active_monsters: Sequence[Monster]
    ) -> None:
        """Reset status icons for monsters."""
        # Remove all existing icons
        for ui in self._tracker._monster_ui.values():
            for icon in ui.status_icons:
                icon.kill()
            ui.status_icons = []

        # Recreate icons and add to sprite layer
        self.create_icon_cache(active_monsters)
        self.add_all_icons()

    def add_all_icons(self) -> None:
        """Add all status icons to the sprite layer."""
        for ui in self._tracker._monster_ui.values():
            for icon in ui.status_icons:
                self.add_icon(icon)

    def add_icon(self, icon: Sprite) -> None:
        """Add a status icon to the sprite layer."""
        if icon.image.get_alpha() == 0:
            icon.image.set_alpha(255)
        self._state.sprites.add(icon, layer=self._layer)

    def remove_monster_icons(self, monster: Monster) -> None:
        """Remove all icons associated with a specific monster."""
        ui = self._tracker._monster_ui.get(monster)
        if ui:
            for icon in ui.status_icons:
                icon.kill()
            ui.status_icons = []

    def get_icons_for_monster(self, monster: Monster) -> list[Sprite]:
        """Retrieve the list of icons for a specific monster."""
        ui = self._tracker._monster_ui.get(monster)
        return ui.status_icons if ui else []

    def animate_icons(
        self, monster: Monster, animate_func: Callable[..., Animation]
    ) -> None:
        for icon in self.get_icons_for_monster(monster):
            alpha = icon.image.get_alpha()
            if alpha == 255:
                animate_func(icon.image, initial=255, set_alpha=0, duration=2)
            elif alpha == 0:
                animate_func(icon.image, initial=0, set_alpha=255, duration=2)
            else:
                icon.image.set_alpha(255)

    def get_icon_position(
        self, monster: Monster, index: int
    ) -> tuple[float, float]:
        owner = monster.get_owner()
        layout_data = self._layouts.get(owner, {})
        key = f"monster_status_icon_slot_{index}"
        rects = layout_data.get(key, [])

        if not rects:
            logger.warning(
                f"No layout rects found for key '{key}' (owner: {owner})"
            )
            return (0, 0)

        position = rects[0].topleft
        logger.debug(
            f"Icon position for monster '{monster}' (owner: {owner}, index: {index}) "
            f"resolved to {position} using key '{key}'"
        )
        return position

    def recalculate_icon_positions(self) -> None:
        for monster, ui in self._tracker._monster_ui.items():
            index = ui.slot_index
            pos = self.get_icon_position(monster, index)
            for icon in ui.status_icons:
                icon.rect.center = pos
