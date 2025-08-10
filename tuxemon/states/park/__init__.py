# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import Session

MenuGameObj = Callable[[], object]


class ParkState(PygameMenuState):
    """
    This state is responsible for the park menu.
    """

    name: ClassVar[str] = "ParkState"

    def __init__(self, session: Session) -> None:
        self.session = session
        self.park_session = session.client.park_session
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MISSIONS)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: pygame_menu.Menu) -> None:
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
