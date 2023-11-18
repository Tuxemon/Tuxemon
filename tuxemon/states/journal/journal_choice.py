# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MAX_PAGE = 20


MenuGameObj = Callable[[], object]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class JournalChoice(PygameMenuState):
    """Shows journal (screen 1/3)."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: list[MonsterModel],
    ) -> None:
        player = local_session.player
        width = menu._width
        height = menu._height

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        total_monster = len(monsters)
        # defines number of pages based on the total nr of monsters
        # it uses math.ceil because if the diff is < .5 , it must
        # round up (eg. 11.49 > 12)
        diff = math.ceil(total_monster / MAX_PAGE)
        menu._column_max_width = [
            fix_measure(width, 0.40),
            fix_measure(width, 0.40),
        ]

        for page in range(diff):
            maximum = (page * MAX_PAGE) + MAX_PAGE
            minimum = page * MAX_PAGE
            _tuxepedia = [
                ele
                for ele in monsters
                if page * MAX_PAGE < ele.txmn_id <= (page + 1) * MAX_PAGE
                and ele.slug in player.tuxepedia
            ]
            tuxepedia = True if _tuxepedia else False
            label = T.format(
                "page_tuxepedia", {"a": str(minimum), "b": str(maximum)}
            ).upper()
            if tuxepedia:
                menu.add.button(
                    label,
                    change_state(
                        "JournalState",
                        kwargs={"monsters": monsters, "page": page},
                    ),
                    font_size=20,
                ).translate(
                    fix_measure(width, 0.18), fix_measure(height, 0.01)
                )
            else:
                lab1 = menu.add.label(
                    label,
                    font_color=(105, 105, 105),
                    font_size=20,
                )
                assert not isinstance(lab1, list)
                lab1.translate(
                    fix_measure(width, 0.18), fix_measure(height, 0.01)
                )

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_generic.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_LEFT

        columns = 2

        monsters = list(db.database["monster"])
        box: list[MonsterModel] = []
        for mov in monsters:
            results = db.lookup(mov, table="monster")
            if results.txmn_id > 0:
                box.append(results)

        diff = round(len(box) / MAX_PAGE) + 1
        rows = int(diff / columns) + 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        self.add_menu_items(self.menu, box)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
