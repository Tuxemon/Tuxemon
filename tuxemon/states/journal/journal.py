# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.db import MonsterModel, SeenStatus
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MAX_PAGE = 20

MenuGameObj = Callable[[], object]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class JournalState(PygameMenuState):
    """Shows journal (screen 2/3)."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: list[MonsterModel],
    ) -> None:
        width = menu._width
        height = menu._height
        menu._column_max_width = [
            fix_measure(width, 0.35),
            fix_measure(width, 0.35),
        ]

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        monsters = sorted(monsters, key=lambda x: x.txmn_id)

        player = local_session.player
        for mon in monsters:
            if mon.slug in player.tuxepedia:
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                if player.tuxepedia[mon.slug] == SeenStatus.seen:
                    menu.add.button(
                        label,
                        change_state(
                            "JournalInfoState",
                            kwargs={"monster": mon},
                        ),
                        font_size=self.font_size_small,
                        font_color=(25, 25, 112, 1),
                        selection_color=(25, 25, 112, 1),
                        button_id=mon.slug,
                    ).translate(
                        fix_measure(width, 0.25), fix_measure(height, 0.01)
                    )
                elif player.tuxepedia[mon.slug] == SeenStatus.caught:
                    menu.add.button(
                        label,
                        change_state(
                            "JournalInfoState",
                            kwargs={"monster": mon},
                        ),
                        font_size=self.font_size_small,
                        button_id=mon.slug,
                        underline=True,
                    ).translate(
                        fix_measure(width, 0.25), fix_measure(height, 0.01)
                    )
            else:
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                lab = menu.add.label(
                    label,
                    font_size=self.font_size_small,
                    font_color=(105, 105, 105),
                    label_id=mon.slug,
                )
                assert not isinstance(lab, list)
                lab.translate(
                    fix_measure(width, 0.25), fix_measure(height, 0.01)
                )

    def __init__(self, **kwargs: Any) -> None:
        monsters: list[MonsterModel] = []
        page: int = 0
        for ele in kwargs.values():
            monsters = ele["monsters"]
            page = ele["page"]

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

        # defines range txmn_ids
        min_txmn: int = 0
        max_txmn: int = 0
        if page == 0:
            min_txmn = 0
            max_txmn = MAX_PAGE
        else:
            min_txmn = page * MAX_PAGE
            max_txmn = (page + 1) * MAX_PAGE

        # applies range to tuxemon
        monster_list = [
            ele for ele in monsters if min_txmn < ele.txmn_id <= max_txmn
        ]

        # fix columns and rows
        num_mon: int = 0
        if len(monster_list) != MAX_PAGE:
            num_mon = len(monster_list) + 1
        else:
            num_mon = len(monster_list)
        rows = num_mon / columns

        super().__init__(
            height=height, width=width, columns=columns, rows=int(rows)
        )

        self.add_menu_items(self.menu, monster_list)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
