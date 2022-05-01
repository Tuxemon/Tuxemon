from __future__ import annotations

from typing import Any, Callable, Generator, Optional, Sequence, Tuple

import pygame
import pygame_menu
from tuxemon.menu.events import playerinput_to_event
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.events import PlayerInput

ChoiceMenuGameObj = Callable[[], None]


class ChoiceState(PygameMenuState):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    def startup(
        self,
        *,
        menu: Sequence[Tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        super().startup(**kwargs)

        for _key, label, callback in menu:
            self.menu.add.button(label, callback)

        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(*widgets_size)

        self.escape_key_exits = escape_key_exits
