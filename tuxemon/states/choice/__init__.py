from __future__ import annotations

from typing import Any, Callable, Generator, Optional, Sequence, Tuple

import pygame
import pygame_menu

from tuxemon.animation import Animation
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

    def __init__(
        self,
        menu: Sequence[Tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        for _key, label, callback in menu:
            self.menu.add.button(label, callback)

        self.animation_size = 0.0
        self.escape_key_exits = escape_key_exits

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(
            max(1, int(widgets_size[0] * self.animation_size)),
            max(1, int(widgets_size[1] * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0

        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.update_callback = self.update_animation_size

        return ani
