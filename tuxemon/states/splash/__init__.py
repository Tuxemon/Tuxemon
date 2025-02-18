# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon import prepare, state
from tuxemon.platform.events import PlayerInput
from tuxemon.states.transition.fade import FadeOutTransition

logger = logging.getLogger(__name__)


class SplashState(state.State):
    """The state responsible for the splash screen."""

    default_duration = 3

    def __init__(self, parent: state.StateManager) -> None:
        super().__init__()

        self.parent = parent

        # this task will skip the splash screen after some time
        self.task(self.fade_out, self.default_duration)
        self.triggered = False

        width, height = prepare.SCREEN_SIZE

        # The space between the edge of the screen
        splash_border = int(prepare.SCREEN_SIZE[0] / 20)

        # Set up the splash screen logos
        logo = self.load_sprite(prepare.PYGAME_LOGO)
        logo.rect.topleft = (
            splash_border,
            height - splash_border - logo.rect.height,
        )

        # Set up the splash screen logos
        cc = self.load_sprite(prepare.CREATIVE_COMMONS)
        cc.rect.topleft = (
            width - splash_border - cc.rect.width,
            height - splash_border - cc.rect.height,
        )
        self.client.sound_manager.play_sound("sound_ding")

    def resume(self) -> None:
        if self.triggered:
            self.parent.pop_state()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # Skip the splash screen if a key is pressed.
        if event.pressed and not self.triggered:
            self.fade_out()
        return None

    def draw(self, surface: pygame.surface.Surface) -> None:
        if not self.triggered:
            surface.fill(prepare.BLACK_COLOR)
            self.sprites.draw(surface)

    def fade_out(self) -> None:
        self.triggered = True
        self.parent.push_state(FadeOutTransition())
