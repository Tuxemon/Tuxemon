# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_JOURNAL_CHOICE, DIMGRAY_COLOR
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC

MAX_PAGE = 20


MenuGameObj = Callable[[], object]
lookup_cache: dict[str, MonsterModel] = {}


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }


class JournalChoice(PygameMenuState):
    """Shows journal (screen 1/3)."""

    name: ClassVar[str] = "JournalChoice"

    def add_menu_items(
        self,
        menu: Menu,
        monsters: list[MonsterModel],
    ) -> None:

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        total_monster = len(monsters)
        pages = math.ceil(total_monster / MAX_PAGE)

        column_width = fix_measure(menu._width, 0.40)
        btn_x_offset = fix_measure(menu._width, 0.18)
        btn_y_offset = fix_measure(menu._height, 0.01)
        menu._column_max_width = [column_width, column_width]

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
                    font_size=self.font_type.small,
                ).translate(btn_x_offset, btn_y_offset)
            else:
                lab1: Any = menu.add.label(
                    label,
                    font_color=DIMGRAY_COLOR,
                    font_size=self.font_type.small,
                )
                lab1.translate(btn_x_offset, btn_y_offset)

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character

        if not lookup_cache:
            _lookup_monsters()

        width, height = client.context.resolution

        columns = 2

        box = list(lookup_cache.values())
        diff = round(len(box) / MAX_PAGE) + 1
        rows = int(diff / columns) + 1

        super().__init__(
            client=client,
            height=height,
            width=width,
            columns=columns,
            rows=rows,
            **kwargs,
        )

        theme = self._setup_theme(BG_JOURNAL_CHOICE)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_LEFT
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, box)
        self.reset_theme()
