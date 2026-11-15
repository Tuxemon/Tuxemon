# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.session import Session

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class ParkState(PygameMenuState):
    """
    This state is responsible for the park menu.
    """

    name: ClassVar[str] = "ParkState"

    def __init__(
        self, client: BaseClient, session: Session, **kwargs: Any
    ) -> None:
        self.session = session
        self.park_session = session.client.park_session
        width, height = client.context.resolution
        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:
        tracker = self.park_session.tracker
        history = self.park_session.encounter_history

        menu.add.label(
            T.translate("menu_park_summary"),
            selectable=True,
            font_size=self.font_type.big,
        )
        menu.add.vertical_margin(10)

        successful = tracker.successful_captures
        failed = tracker.failed_attempts
        total = successful + failed
        rate = tracker.get_capture_rate()
        unique_seen = tracker.unique_count

        menu.add.vertical_margin(10)
        menu.add.label(
            f"{T.translate('menu_park_seen')}: {unique_seen}",
            font_size=self.font_type.small,
        )
        menu.add.label(
            f"{T.translate('menu_park_total')}: {total}",
            font_size=self.font_type.small,
        )
        menu.add.label(
            f"{T.translate('menu_park_capture')}: {successful}",
            font_size=self.font_type.small,
        )
        menu.add.label(
            f"{T.translate('menu_park_failed')}: {failed}",
            font_size=self.font_type.small,
        )
        menu.add.label(
            f"{T.translate('menu_park_success_rate')}: {rate * 100:.1f}%",
            font_size=self.font_type.small,
        )

        menu.add.vertical_margin(10)
        menu.add.label(f"{T.translate('menu_park_sighting')}", selectable=True)
        most_frequent = tracker.get_most_frequent_sightings()

        if most_frequent:
            for slug, count in most_frequent:
                menu.add.label(
                    f"• {T.translate(slug)}: seen {count} times",
                    font_size=self.font_type.small,
                )
        else:
            menu.add.label(T.translate("menu_park_no_sighting"))

        menu.add.vertical_margin(10)
        menu.add.label(
            f"{T.translate('menu_park_highlights')}:", selectable=True
        )

        if history:
            for slug, encounters in history.items():
                total_turns = sum(e.turns_remaining for e in encounters)
                avg_turns = total_turns / len(encounters)
                menu.add.label(
                    f"{T.translate(slug)}: avg {avg_turns:.1f} turns before ending",
                    font_size=self.font_type.small,
                )
        else:
            menu.add.label(T.translate("menu_park_no_highlights"))

        menu.add.vertical_margin(10)
        menu.add.label(T.translate("menu_park_thanks"), selectable=True)
