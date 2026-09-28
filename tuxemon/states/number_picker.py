# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BG_MISSIONS

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class NumberPickerState(PygameMenuState):
    """
    A compact number picker using +/- buttons instead of a long list.
    """

    name: ClassVar[str] = "NumberPickerState"

    def __init__(
        self,
        client: BaseClient,
        min_value: int,
        max_value: int,
        callback: Callable[[int], None],
        *,
        step: int = 1,
        title: str | None = None,
        escape_key_exits: bool | None = None,
        **kwargs: Any,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.callback = callback
        self.title = title or T.translate("select_number")
        self.current_value = min_value

        width, height = client.context.resolution
        width = int(0.5 * width)
        height = int(0.5 * height)
        super().__init__(client=client, width=width, height=height, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.widget_alignment = ALIGN_CENTER
        theme.scrollarea_position = POSITION_EAST
        theme.title = True
        self._menu_config["theme"] = theme

        if escape_key_exits is not None:
            self.escape_key_exits = escape_key_exits

        self._build_menu()
        self.reset_theme()

    def _build_menu(self) -> None:
        self.menu.clear()
        self.menu.set_title(self.title).center_content()

        row = self.menu.add.frame_h(300, 70)
        row._relax = True

        self.menu.add.label(
            T.translate("number_picker_instructions"),
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
        )

        row.pack(
            self.menu.add.label("-"),
            align=ALIGN_CENTER,
        )

        self.value_label: Any = self.menu.add.label(
            str(self.current_value),
            font_size=self.font_type.big,
        )
        row.pack(self.value_label, align=ALIGN_CENTER)

        row.pack(
            self.menu.add.label("+"),
            align=ALIGN_CENTER,
        )

    def _increment(self) -> None:
        new_value = self.current_value + self.step
        if new_value <= self.max_value:
            self.current_value = new_value
            self.value_label.set_title(str(self.current_value))

    def _decrement(self) -> None:
        new_value = self.current_value - self.step
        if new_value >= self.min_value:
            self.current_value = new_value
            self.value_label.set_title(str(self.current_value))

    def _confirm(self) -> None:
        self.client.pop_state(self)
        self.callback(self.current_value)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # RIGHT increment
        if event.button == buttons.RIGHT and self.valid_press(event):
            self._increment()
            return None

        # LEFT decrement
        if event.button == buttons.LEFT and self.valid_press(event):
            self._decrement()
            return None

        # A confirm
        if event.button == buttons.A and event.pressed:
            self._confirm()
            return None

        # B cancel
        if event.button == buttons.B and event.pressed:
            self.client.pop_state(self)
            return None

        return event
