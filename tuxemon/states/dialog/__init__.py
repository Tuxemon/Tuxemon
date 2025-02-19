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
from tuxemon.ui.text import TextArea

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
        colors: dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.text_queue = list(text)
        self.avatar = avatar
        self.character_delay = DEFAULT_CHARACTER_DELAY

        default_colors: dict[str, Any] = {
            "bg_color": self.background_color,
            "font_color": self.font_color,
            "font_shadow": self.font_shadow_color,
            "border": self.borders_filename,
        }
        colors = colors or {}
        final_colors = default_colors.copy()
        final_colors.update(colors)

        _border = load_and_scale(final_colors["border"])
        self.window._set_border(_border)
        self.window._color = final_colors["bg_color"]

        self.dialog_box = TextArea(
            self.font, final_colors["font_color"], final_colors["font_shadow"]
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
