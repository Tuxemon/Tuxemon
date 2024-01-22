# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.db import MonsterModel, SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
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
                param = {"monster": mon}
                label = f"{mon.txmn_id}. {T.translate(mon.slug).upper()}"
                if player.tuxepedia[mon.slug] == SeenStatus.seen:
                    menu.add.button(
                        label,
                        change_state("JournalInfoState", kwargs=param),
                        font_size=self.font_size_small,
                        button_id=mon.slug,
                    ).translate(
                        fix_measure(width, 0.25), fix_measure(height, 0.01)
                    )
                elif player.tuxepedia[mon.slug] == SeenStatus.caught:
                    menu.add.button(
                        label + "◉",
                        change_state("JournalInfoState", kwargs=param),
                        font_size=self.font_size_small,
                        button_id=mon.slug,
                        underline=True,
                    ).translate(
                        fix_measure(width, 0.25), fix_measure(height, 0.01)
                    )
            else:
                label = f"{mon.txmn_id}. -----"
                lab: Any = menu.add.label(
                    label,
                    font_size=self.font_size_small,
                    font_color=prepare.DIMGRAY_COLOR,
                    label_id=mon.slug,
                )
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
            image_path=tools.transform_resource_filename(prepare.BG_JOURNAL),
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

        self._page = page
        self._monster_list = monster_list
        self.add_menu_items(self.menu, monster_list)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        client = self.client

        monsters = list(db.database["monster"])
        box: list[MonsterModel] = []
        for mov in monsters:
            results = db.lookup(mov, table="monster")
            if results.txmn_id > 0:
                box.append(results)

        max_page = round(len(box) / MAX_PAGE)
        param: dict[str, Any] = {}
        param["monsters"] = box
        if event.button == buttons.RIGHT and event.pressed:
            if self._page < (max_page - 1):
                self._page += 1
                param["page"] = self._page
                client.replace_state("JournalState", kwargs=param)
            else:
                param["page"] = 0
                client.replace_state("JournalState", kwargs=param)
        elif event.button == buttons.LEFT and event.pressed:
            if self._page > 0:
                self._page -= 1
                param["page"] = self._page
                client.replace_state("JournalState", kwargs=param)
            else:
                param["page"] = max_page - 1
                client.replace_state("JournalState", kwargs=param)
        elif (
            event.button == buttons.BACK or event.button == buttons.B
        ) and event.pressed:
            client.pop_state()
        else:
            return super().process_event(event)
        return None
