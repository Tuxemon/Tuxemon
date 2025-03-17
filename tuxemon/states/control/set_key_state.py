# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame
from pygame_menu import locals

from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.events import PlayerInput


class SetKeyState(PygameMenuState):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    def __init__(self, value: str, **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        super().__init__(**kwargs)
        self.menu.add.label(T.translate("options_new_input_key0").upper())
        self.value = value
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        invalid_keys = [
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_RSHIFT,
            pygame.K_LSHIFT,
            pygame.K_RETURN,
            pygame.K_ESCAPE,
            pygame.K_BACKSPACE,
        ]

        pressed_key = next(
            (
                k
                for k in range(len(pygame.key.get_pressed()))
                if pygame.key.get_pressed()[k]
            ),
            None,
        )

        if (
            isinstance(pressed_key, int)
            and (event.pressed or event.value == "")
            and pressed_key not in invalid_keys
        ):
            assert pressed_key
            self.client.pop_state()
            pressed_key_str = pygame.key.name(pressed_key)
            if event.value == pressed_key_str:
                # Update the configuration file with the new key
                self.client.config.update_control(self.value, pressed_key)
                return event

        return None

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
