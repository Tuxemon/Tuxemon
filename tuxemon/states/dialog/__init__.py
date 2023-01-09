# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, Tuple

from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.states.choice import ChoiceState
from tuxemon.ui.text import TextArea


class DialogState(PopUpMenu):
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
        menu: Optional[Sequence[Tuple[str, str, Callable[[], None]]]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.text_queue = list(text)
        self.avatar = avatar
        self.menu = menu
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.calc_internal_rect()
        self.sprites.add(self.text_area)

        if self.avatar:
            avatar_rect = self.calc_final_rect()
            self.avatar.rect.bottomleft = avatar_rect.left, avatar_rect.top
            self.sprites.add(self.avatar)

    def on_open(self) -> None:
        self.next_text()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:

        if event.pressed and event.button == buttons.A:
            if self.text_area.drawing_text:
                self.character_delay = 0.001

            elif self.next_text() is None:
                if self.menu:
                    self.client.push_state(
                        ChoiceState(
                            menu=self.menu,
                            rect=self.text_area.rect,
                        )
                    )
                else:
                    self.client.pop_state(self)

        return None

    def next_text(self) -> Optional[str]:
        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            return None
