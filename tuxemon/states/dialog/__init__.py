# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.graphics import load_and_scale
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.tools import scale
from tuxemon.ui.text import TextArea
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite


DEFAULT_CHARACTER_DELAY: float = 0.05
CHARACTER_DELAY: float = 0.001


class DialogState(PopUpMenu[None]):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    def __init__(
        self,
        text: Sequence[str] = (),
        avatar: Optional[Sprite] = None,
        box_style: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.text_queue = list(text)
        self.avatar = avatar
        self.character_delay = DEFAULT_CHARACTER_DELAY

        default_box_style: dict[str, Any] = {
            "bg_color": self.background_color,
            "font_color": self.font_color,
            "font_shadow": self.font_shadow_color,
            "border": self.borders_filename,
            "line_spacing": 0,
            "h_alignment": HorizontalAlignment.LEFT,
            "v_alignment": VerticalAlignment.TOP,
        }

        final_box_style = default_box_style.copy()
        box_style = box_style or {}
        final_box_style.update(box_style)

        _border = load_and_scale(final_box_style["border"])
        self.window._set_border(_border)
        self.window._color = final_box_style["bg_color"]
        line_spacing = scale(final_box_style["line_spacing"])

        self.dialog_box = TextArea(
            font=self.font,
            font_color=final_box_style["font_color"],
            font_shadow=final_box_style["font_shadow"],
            h_alignment=final_box_style["h_alignment"],
            v_alignment=final_box_style["v_alignment"],
            line_spacing=line_spacing,
        )
        self.dialog_box.rect = self.calc_internal_rect()
        self.sprites.add(self.dialog_box)

        if self.avatar:
            avatar_rect = self.calc_final_rect()
            self.avatar.rect.bottomleft = avatar_rect.left, avatar_rect.top
            self.sprites.add(self.avatar)

    def on_open(self) -> None:
        self.next_text()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.pressed and event.button == buttons.A:
            if self.dialog_box.drawing_text:
                self.character_delay = CHARACTER_DELAY
            elif not self.dialog_box.drawing_text:
                self.next_text()

        return None

    def next_text(self) -> Optional[str]:
        if self.dialog_box.drawing_text:
            return None

        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            self.client.pop_state(self)
            return None
