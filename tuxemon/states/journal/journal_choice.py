# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState

if TYPE_CHECKING:
    from tuxemon.npc import NPC

MAX_PAGE = 20


MenuGameObj = Callable[[], object]
lookup_cache: dict[str, MonsterModel] = {}


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results


class JournalChoice(PygameMenuState):
    """Shows journal (screen 1/3)."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: list[MonsterModel],
    ) -> None:
        width = menu._width
        height = menu._height

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        total_monster = len(monsters)
        pages = math.ceil(total_monster / MAX_PAGE)

        menu._column_max_width = [
            fix_measure(width, 0.40),
            fix_measure(width, 0.40),
        ]

        for page in range(pages):
            start = page * MAX_PAGE
            end = min(start + MAX_PAGE, total_monster)
            tuxepedia = [
                mon
                for mon in monsters
                if start < mon.txmn_id <= end
                and self.char.tuxepedia.is_registered(mon.slug)
            ]
            label = T.format(
                "page_tuxepedia", {"a": str(start), "b": str(end)}
            ).upper()

            if tuxepedia:
                menu.add.button(
                    label,
                    change_state(
                        "JournalState",
                        character=self.char,
                        monsters=monsters,
                        page=page,
                    ),
                    font_size=self.font_size_small,
                ).translate(
                    fix_measure(width, 0.18), fix_measure(height, 0.01)
                )
            else:
                lab1: Any = menu.add.label(
                    label,
                    font_color=prepare.DIMGRAY_COLOR,
                    font_size=self.font_size_small,
                )
                lab1.translate(
                    fix_measure(width, 0.18), fix_measure(height, 0.01)
                )

    def __init__(self, character: NPC) -> None:
        if not lookup_cache:
            _lookup_monsters()
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_JOURNAL_CHOICE)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_LEFT

        self.char = character

        columns = 2

        box = list(lookup_cache.values())
        diff = round(len(box) / MAX_PAGE) + 1
        rows = int(diff / columns) + 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        self.add_menu_items(self.menu, box)
        self.reset_theme()
