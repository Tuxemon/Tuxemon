# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.celestial_handler import get_phase_progress
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.session import Session

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class CelestialState(PygameMenuState):
    """
    Displays all celestial bodies, their current phases, and progress bars.
    """

    name: ClassVar[str] = "CelestialState"

    def __init__(
        self, client: BaseClient, session: Session, **kwargs: Any
    ) -> None:
        self.session = session
        self.celestial = session.celestial

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
        day_of_year = self.session.time.get_time_variables().day_of_year

        menu.add.label(
            T.translate("menu_celestial_title"),
            selectable=True,
            font_size=self.font_type.big,
        )
        menu.add.vertical_margin(10)

        # Current phases
        menu.add.label(
            T.translate("menu_celestial_current"),
            font_size=self.font_type.medium,
        )
        menu.add.vertical_margin(5)

        for cycle in self.celestial._cycles:
            phase, day_in_phase, phase_length = get_phase_progress(
                day_of_year, cycle
            )

            menu.add.label(
                f"{T.translate(cycle.name)} — {T.translate(phase)}",
                selectable=True,
                font_size=self.font_type.small,
            )
            menu.add.progress_bar(
                f"{day_in_phase + 1}/{phase_length}",
                (day_in_phase / phase_length) * 100,
            )
            menu.add.vertical_margin(10)

        # Detailed cycle breakdown
        menu.add.vertical_margin(15)
        menu.add.label(
            T.translate("menu_celestial_details"),
            selectable=True,
            font_size=self.font_type.medium,
        )
        menu.add.vertical_margin(5)

        for cycle in self.celestial._cycles:
            menu.add.label(
                f"{T.translate(cycle.name)} — {cycle.length}",
                selectable=True,
                font_size=self.font_type.small,
            )

            for length, phase_name in cycle.phase_data:
                menu.add.label(
                    f"• {T.translate(phase_name)} ({length})",
                    font_size=self.font_type.small,
                )

            menu.add.vertical_margin(10)

        menu.add.label(
            T.translate("menu_celestial_footer"),
            selectable=True,
            font_size=self.font_type.medium,
        )
