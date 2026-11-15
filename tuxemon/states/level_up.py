# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS

_STAT_DISPLAY_ORDER = ["hp", "armour", "dodge", "melee", "ranged", "speed"]

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.monster.monster import Monster


class LevelUpSummaryState(PygameMenuState):
    """
    UI state that displays stat changes after a monster gains one or more levels.
    This state is shown after combat or after any XP gain outside combat.
    """

    name: ClassVar[str] = "LevelUpSummaryState"

    def __init__(
        self,
        client: BaseClient,
        monster: Monster,
        start_level: int,
        end_level: int,
        diff: dict[str, tuple[int, int, int]],
        *,
        use_relative_position: bool = False,
        **kwargs: Any,
    ) -> None:
        self.monster = monster
        self.start_level = start_level
        self.end_level = end_level
        self.diff = diff

        width, height = client.context.resolution

        super().__init__(
            client=client,
            height=int(height // 1.5),
            width=int(width // 2),
            **kwargs,
        )

        theme = self._setup_theme(BG_MISSIONS)
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme
        self._build_menu(self.menu)

        if use_relative_position:
            self.menu.set_relative_position(50, 25)

        self.reset_theme()

    def _build_menu(self, menu: Menu) -> None:

        menu.add.label(
            title=self.monster.name.upper(),
            font_size=self.font_type.medium,
        )

        menu.add.label(
            title=f"Lv.{self.start_level} → Lv.{self.end_level}",
            font_size=self.font_type.small,
        )

        menu.add.vertical_margin(10)

        for stat_name in _STAT_DISPLAY_ORDER:
            if stat_name not in self.diff:
                continue
            old, new, delta = self.diff[stat_name]
            sign = "+" if delta > 0 else ""
            label = T.translate(stat_name).upper()
            text = f"{label}: {old} → {new} ({sign}{delta})"
            menu.add.label(text, font_size=self.font_type.small)

        menu.add.vertical_margin(10)

        menu.add.button(
            title=T.translate("ok").upper(),
            action=self._confirm,
            font_size=self.font_type.small,
        )

    def _confirm(self) -> None:
        self.client.pop_state()
