#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.DialogState Handles the dialogue
#
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
