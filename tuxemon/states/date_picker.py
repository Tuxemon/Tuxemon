# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.platform.const.sizes import MONTH_KEYS

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class DatePickerState(PygameMenuState):
    name: ClassVar[str] = "DatePickerState"

    def __init__(
        self,
        client: BaseClient,
        callback: Callable[[tuple[int, int]], None],
        **kwargs: Any,
    ):
        self.callback = callback
        self.selected_month: int | None = None
        width, height = client.context.resolution
        escape_key_exits = kwargs.pop("escape_key_exits", None)

        super().__init__(client=client, width=width, height=height, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.widget_alignment = ALIGN_CENTER
        theme.scrollarea_position = POSITION_EAST
        theme.title = True
        self._menu_config["theme"] = theme

        if escape_key_exits is not None:
            self.escape_key_exits = escape_key_exits
        self._build_month_menu()
        self.reset_theme()

    def _build_month_menu(self) -> None:
        self.menu.clear()
        self.menu.set_title(T.translate("select_month")).center_content()

        for index, key in enumerate(MONTH_KEYS, start=1):
            self.menu.add.button(
                T.translate(key), lambda m=index: self._pick_month(m)
            )

    def _pick_month(self, month: int) -> None:
        self.selected_month = month

        # Determine max days
        if month in (4, 6, 9, 11):
            max_days = 30
        elif month == 2:
            max_days = 29
        else:
            max_days = 31

        self.client.push_state(
            "NumberPickerState",
            min_value=1,
            max_value=max_days,
            callback=self._pick_day,
            title=T.translate("select_day"),
        )

    def _pick_day(self, day: int) -> None:
        assert self.selected_month is not None
        self.callback((self.selected_month, day))
        self.client.pop_state()
