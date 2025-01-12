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


class DialogState(PopUpMenu[None]):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close

    """

    default_character_delay = 0.05

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

        bg_color = self.background_color
        font_color = self.font_color
        font_shadow = self.font_shadow_color
        border = self.borders_filename

        bg_color = colors["bg_color"] if colors else bg_color
        font_color = colors["font_color"] if colors else font_color
        font_shadow = colors["font_shadow"] if colors else font_shadow
        border = colors["border"] if colors else border

        _border = load_and_scale(border)
        self.window._set_border(_border)

        self.dialog_box = TextArea(self.font, font_color, font_shadow)
        self.dialog_box.rect = self.calc_internal_rect()
        self.sprites.add(self.dialog_box)
        self.window._color = bg_color

        if self.avatar:
            avatar_rect = self.calc_final_rect()
            self.avatar.rect.bottomleft = avatar_rect.left, avatar_rect.top
            self.sprites.add(self.avatar)

    def on_open(self) -> None:
        self.next_text()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.pressed and event.button == buttons.A:
            if self.dialog_box.drawing_text:
                self.character_delay = 0.001

            elif self.next_text() is None:
                self.client.pop_state(self)

        return None

    def next_text(self) -> Optional[str]:
        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            return None
