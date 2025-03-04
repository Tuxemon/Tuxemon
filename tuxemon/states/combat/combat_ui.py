# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon import tools
from tuxemon.menu.interface import ExpBar, HpBar
from tuxemon.sprite import Sprite

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
