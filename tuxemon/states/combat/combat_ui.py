# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon import prepare, tools
from tuxemon.menu.interface import ExpBar, HpBar
from tuxemon.sprite import Sprite
from tuxemon.state import State

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.monster import Monster


class CombatUI:
    """
    A class responsible for drawing the combat UI, including HP and EXP bars.
    """

    def __init__(self) -> None:
        self._hp_bars: MutableMapping[Monster, HpBar] = {}
        self._exp_bars: MutableMapping[Monster, ExpBar] = {}

    def draw_hp_bars(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws the HP bars for each monster in the hud dictionary.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        show_player_hp = graphics.hud.hp_bar_player
        show_opponent_hp = graphics.hud.hp_bar_opponent

        for monster, _sprite in hud.items():
            if _sprite.player and show_player_hp:
                rect = self.create_rect_for_bar(_sprite, 70, 8, 18)
            elif not _sprite.player and show_opponent_hp:
                rect = self.create_rect_for_bar(_sprite, 70, 8, 12)
            else:
                continue
            self._hp_bars[monster].draw(_sprite.image, rect)

    def draw_exp_bars(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws the EXP bars for each player monster in the hud dictionary.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        show_player_exp = graphics.hud.exp_bar_player

        for monster, _sprite in hud.items():
            if _sprite.player and show_player_exp:
                rect = self.create_rect_for_bar(_sprite, 70, 6, 31)
                self._exp_bars[monster].draw(_sprite.image, rect)

    def create_rect_for_bar(
        self, hud: Sprite, width: int, height: int, top_offset: int = 0
    ) -> Rect:
        """
        Creates a Rect object for a bar.

        Parameters:
            hud: The sprite for the monster.
            width: The width of the bar.
            height: The height of the bar.
            top_offset: The top offset of the bar. Defaults to 0.

        Returns:
            A Rect object representing the bar.
        """
        rect = Rect(0, 0, tools.scale(width), tools.scale(height))
        rect.right = hud.image.get_width() - tools.scale(8)
        rect.top += tools.scale(top_offset)
        return rect

    def draw_all_ui(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws all the UI elements, including HP and EXP bars.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        self.draw_hp_bars(graphics, hud)
        self.draw_exp_bars(graphics, hud)


class CombatStatusIcon:
    """Handles creation, caching, and updating of status icons."""

    def __init__(self, state: State) -> None:
        self.state = state
        self._status_icon_cache: dict[
            tuple[str, tuple[float, float]], Sprite
        ] = {}
        self._status_icons: dict[Monster, list[Sprite]] = {}

    def determine_icon_position(
        self,
        monster: Monster,
        monsters_in_play: Sequence[Monster],
        base_monsters: Sequence[Monster],
    ) -> tuple[float, float]:
        icon_positions = {
            (True, 1): prepare.ICON_OPPONENT_SLOT,
            (True, 0): prepare.ICON_OPPONENT_DEFAULT,
            (False, 1): prepare.ICON_PLAYER_SLOT,
            (False, 0): prepare.ICON_PLAYER_DEFAULT,
        }
        return icon_positions[
            (
                monsters_in_play == base_monsters,
                monsters_in_play.index(monster),
            )
        ]

    def update_icons_for_monsters(
        self,
        active_monsters: Sequence[Monster],
        monsters_left: Sequence[Monster],
        monsters_right: Sequence[Monster],
    ) -> None:
        """Reset status icons for monsters."""
        # remove all status icons
        self.state.sprites.remove(*self._status_icons.values())
        self._status_icons.clear()

        # add status icons
        for monster in active_monsters:
            self._status_icons[monster] = []
            for status in monster.status:
                if status.icon:
                    icon_position = (
                        self.determine_icon_position(
                            monster, monsters_left, monsters_left
                        )
                        if monster in monsters_left
                        else self.determine_icon_position(
                            monster, monsters_right, monsters_left
                        )
                    )
                    cache_key = (status.icon, icon_position)
                    if cache_key not in self._status_icon_cache:
                        self._status_icon_cache[cache_key] = (
                            self.state.load_sprite(
                                status.icon, layer=200, center=icon_position
                            )
                        )

                    icon = self._status_icon_cache[cache_key]
                    self.state.sprites.add(icon, layer=200)
                    self._status_icons[monster].append(icon)

    def remove_monster_icons(self, monster: Monster) -> None:
        if monster in self._status_icons:
            for icon in self._status_icons[monster]:
                icon.kill()
            del self._status_icons[monster]

    def get_icons_for_monster(self, monster: Monster) -> list[Sprite]:
        return self._status_icons.get(monster, [])
