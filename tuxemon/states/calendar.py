# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.platform.const.sizes import MONTH_KEYS
from tuxemon.session import Session

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class CalendarState(PygameMenuState):
    """
    Displays today's date and all monster birthdays in a calendar-like view.
    """

    name: ClassVar[str] = "CalendarState"

    def __init__(
        self, client: BaseClient, session: Session, **kwargs: Any
    ) -> None:
        self.session = session

        width, height = client.context.resolution

        width = int(width * 0.8)
        height = int(height * 0.8)

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:
        today_month, today_day = self.session.time.get_month_day()
        today_month_name = T.translate(MONTH_KEYS[today_month - 1])

        menu.add.label(
            T.translate("menu_calendar_title"),
            selectable=True,
            font_size=self.font_type.big,
        )
        menu.add.vertical_margin(10)

        menu.add.label(
            f"{T.translate('menu_calendar_today')}: "
            f"{today_month_name} {today_day}",
            font_size=self.font_type.medium,
        )
        menu.add.vertical_margin(15)

        monsters = [
            m for m in self.session.player.monsters if m.birthdate is not None
        ]

        monsters.sort(
            key=lambda m: m.birthdate if m.birthdate is not None else (0, 0)
        )

        if not monsters:
            menu.add.label(
                T.translate("menu_calendar_none"),
                font_size=self.font_type.small,
            )
            return

        current_month = None

        for mon in monsters:
            if mon.birthdate is None:
                continue
            month, day = mon.birthdate
            month_name = T.translate(MONTH_KEYS[month - 1])

            if month != current_month:
                current_month = month
                menu.add.vertical_margin(10)
                menu.add.label(
                    f"=== {month_name} ===",
                    font_size=self.font_type.medium,
                    selectable=True,
                )
                menu.add.vertical_margin(5)

            is_today = month == today_month and day == today_day
            label = f"{day} — {mon.name}" + (" *" if is_today else "")

            menu.add.label(
                label,
                selectable=True,
                font_size=self.font_type.small,
            )
            menu.add.vertical_margin(3)
