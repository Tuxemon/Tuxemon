# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon.menu.interface import Bar, ExpBar, HpBar
from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.monster.monster import Monster
    from tuxemon.prepare import DisplayContext


class CombatBars:
    """
    A class responsible for drawing the combat UI, including HP and EXP bars.
    """

    def __init__(self, context: DisplayContext) -> None:
        self.context = context
        self._hp_bars: MutableMapping[Monster, HpBar] = {}
        self._exp_bars: MutableMapping[Monster, ExpBar] = {}

    def draw_bars(
        self,
        hud: MutableMapping[Monster, Sprite],
        graphics: BattleGraphicsModel,
    ) -> None:
        """Called every time the HUD needs a refresh."""
        gh = graphics.hud

        for monster, _sprite in hud.items():
            # Always draw HP bar if graphics available
            if gh.hp_bar_player or gh.hp_bar_opponent:
                top_offset = (
                    gh.hp_player_top if _sprite.player else gh.hp_opponent_top
                )

                rect = self.create_rect_for_bar(
                    _sprite,
                    gh.hp_bar_width,
                    gh.hp_bar_height,
                    top_offset,
                    gh.bar_right_padding,
                )
                # HP is not resynced here: damage lands well before
                # check_party_hp animates it, and that pass covers every
                # monster each round, so the bar corrects itself anyway.
                self.get_hp_bar(monster).draw(_sprite.image, rect)

            # Always draw EXP bar for player if graphics available
            if _sprite.player and gh.exp_bar_player:
                rect = self.create_rect_for_bar(
                    _sprite,
                    gh.hp_bar_width,
                    gh.exp_bar_height,
                    gh.exp_bar_top,
                    gh.bar_right_padding,
                )
                exp_bar = self.get_exp_bar(monster)
                self.resync(exp_bar, monster.experience_progress_percent)
                exp_bar.draw(_sprite.image, rect)

    def create_rect_for_bar(
        self,
        hud: Sprite,
        width: int,
        height: int,
        top: int,
        right_padding: int,
    ) -> Rect:
        s = self.context.scaling.scale_int

        width = s(width)
        height = s(height)
        top = s(top)
        right_padding = s(right_padding)

        rect = Rect(0, 0, width, height)
        rect.top = top
        rect.right = hud.image.get_width() - right_padding
        return rect

    @staticmethod
    def resync(bar: Bar, expected: float) -> None:
        """
        Snap a bar back onto the model unless an animation is heading there.

        A bar is only ever moved by animations, so experience granted without
        one being scheduled (a party member levelling up off the field, say),
        or a chain that was aborted part-way, would otherwise leave the bar
        showing a stale value indefinitely. Comparing against the bar's target
        rather than its current value keeps in-flight animations intact, which
        is what :meth:`claim` is for.
        """
        if not math.isclose(bar.target_value, expected, abs_tol=1e-6):
            bar.sync(expected)

    def get_hp_bar(self, monster: Monster) -> HpBar:
        return self._hp_bars.setdefault(
            monster, HpBar(self.context, monster.hp_ratio)
        )

    def get_exp_bar(self, monster: Monster) -> ExpBar:
        return self._exp_bars.setdefault(
            monster, ExpBar(self.context, monster.experience_progress_percent)
        )

    def claim(self, bar: Bar, expected: float) -> None:
        """
        Announce that an animation will bring ``bar`` to ``expected``.

        Call this as soon as the model changes, even when the animation itself
        only starts seconds later, so redraws in the meantime leave the bar
        alone instead of snapping it to the new value.
        """
        bar.target_value = expected

    def remove_monster(self, monster: Monster) -> None:
        if monster in self._hp_bars:
            logger.debug("Removing HP bar for %s", monster.name)
            self._hp_bars.pop(monster, None)

        if monster in self._exp_bars:
            logger.debug("Removing EXP bar for %s", monster.name)
            self._exp_bars.pop(monster, None)

    def clear_all(self) -> None:
        logger.debug("Clearing all combat bars.")
        self._hp_bars.clear()
        self._exp_bars.clear()
