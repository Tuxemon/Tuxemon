# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import (
    BG_JOURNAL,
    DIMGRAY_COLOR,
    SEA_BLUE_COLOR,
)
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.platform.events import PlayerInput

MAX_PAGE = 20

MenuGameObj = Callable[[], object]


class JournalState(PygameMenuState):
    """Shows journal (screen 2/3)."""

    name: ClassVar[str] = "JournalState"

    def add_menu_items(self, menu: Menu, monsters: list[MonsterModel]) -> None:
        btn_x_offset = fix_measure(menu._width, 0.25) - self.client.context.scaling.scale_int(60)
        btn_y_offset = fix_measure(menu._height, 0.01)
        menu._column_max_width = [None, None]

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        monsters = sorted(monsters, key=lambda x: x.txmn_id)

        for mon in monsters:
            if self.char.tuxepedia.is_registered(mon.slug):
                label = f"{mon.txmn_id}. {T.translate(mon.slug)}"
                if self.char.tuxepedia.is_seen(mon.slug):
                    menu.add.button(
                        label,
                        change_state(
                            "JournalInfoState",
                            character=self.char,
                            monster=mon,
                            source=self.name,
                        ),
                        font_size=self.font_type.biggest,
                        button_id=mon.slug,
                    ).translate(btn_x_offset, btn_y_offset)
                elif self.char.tuxepedia.is_caught(mon.slug):
                    menu.add.button(
                        label + "◉",
                        change_state(
                            "JournalInfoState",
                            character=self.char,
                            monster=mon,
                            source=self.name,
                        ),
                        font_size=self.font_type.biggest,
                        button_id=mon.slug,
                        underline=True,
                        underline_color=SEA_BLUE_COLOR,
                        underline_offset=self.client.context.scaling.scale_int(1),
                        underline_width=self.client.context.scaling.scale_int(1),
                    ).translate(btn_x_offset, btn_y_offset)
            else:
                label = f"{mon.txmn_id}. -----"
                lab: Any = menu.add.label(
                    label,
                    font_size=self.font_type.biggest,
                    font_color=DIMGRAY_COLOR,
                    label_id=mon.slug,
                )
                lab.translate(btn_x_offset, btn_y_offset)

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        monsters: list[MonsterModel],
        page: int,
        select_last: bool = False,
        **kwargs: Any,
    ) -> None:
        MonsterModel.load_cache(db)
        self.cache = MonsterModel.get_cache()

        self.char = character
        self._page = page

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

        self._monster_list = monster_list

        width, height = client.context.resolution

        columns = 2

        # fix columns and rows
        num_mon: int = 0
        if len(monster_list) != MAX_PAGE:
            num_mon = len(monster_list) + 1
        else:
            num_mon = len(monster_list)
        rows = num_mon / columns

        super().__init__(
            client=client,
            height=height,
            width=width,
            columns=columns,
            rows=int(rows),
            **kwargs,
        )

        theme = self._setup_theme(BG_JOURNAL)
        theme.widget_font_shadow = False
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_LEFT
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, monster_list)
        self.reset_theme()

        if select_last:
            selectables = [w for w in self.menu._widgets if w.is_selectable]
            if selectables:
                self.menu.select_widget(selectables[-1])

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        client = self.client
        box = list(self.cache.values())
        max_page = (len(box) + MAX_PAGE - 1) // MAX_PAGE

        # LEFT / RIGHT → page navigation (with repeat)
        if event.button in (buttons.RIGHT, buttons.LEFT) and self.valid_press(
            event
        ):
            self._page = (
                self._page + (1 if event.button == buttons.RIGHT else -1)
            ) % max_page

            client.replace_state(
                "JournalState",
                character=self.char,
                monsters=box,
                page=self._page,
            )
            return None

        # DOWN at last selectable entry (or empty page) → next page
        elif event.button == buttons.DOWN and self.valid_press(event):
            sel = self.menu.get_selected_widget()
            selectables = [w for w in self.menu._widgets if w.is_selectable]
            if not selectables or sel is selectables[-1]:
                self._page = (self._page + 1) % max_page
                client.replace_state(
                    "JournalState",
                    character=self.char,
                    monsters=box,
                    page=self._page,
                )
                return None

        # UP at first selectable entry (or empty page) → previous page
        elif event.button == buttons.UP and self.valid_press(event):
            sel = self.menu.get_selected_widget()
            selectables = [w for w in self.menu._widgets if w.is_selectable]
            if not selectables or sel is selectables[0]:
                self._page = (self._page - 1) % max_page
                client.replace_state(
                    "JournalState",
                    character=self.char,
                    monsters=box,
                    page=self._page,
                    select_last=True,
                )
                return None

        # B / BACK → close (pressed only)
        elif event.button in (buttons.BACK, buttons.B) and event.pressed:
            client.remove_state_by_name("JournalState")
            return None

        # Everything else → normal menu behavior (UP/DOWN, A, etc.)
        return super().process_event(event)
