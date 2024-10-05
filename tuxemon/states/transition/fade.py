# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Optional

import pygame

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class FadeTransitionBase(State):
    """The state responsible for the battle transitions."""

    force_draw = True
    state_duration = 1.0
    fade_duration = 1.5

    def __init__(
        self,
        state_duration: Optional[float] = None,
        fade_duration: Optional[float] = None,
        caller: Optional[State] = None,
        color: ColorLike = prepare.BLACK_COLOR,
    ) -> None:
        """
        Parameters:
            state_duration: The duration of the transition state in seconds.
                If not provided, a default value will be used.
            fade_duration: The duration of the fade animation in seconds.
                If not provided, a default value will be used.
            caller: The state that initiated the transition. If not provided,
                it will be set to None.
            color: The color to use for the fade transition. Defaults to black.
        """
        super().__init__()

        logger.debug("Initializing fade transition")

        if state_duration is not None:
            self.state_duration = state_duration

        if fade_duration is not None:
            self.fade_duration = fade_duration

        self.caller = caller
        size = self.client.screen.get_size()
        self.transition_surface = pygame.Surface(size, pygame.SRCALPHA)
        self.transition_surface.fill(color)
        self.task(self.client.pop_state, self.state_duration)
        self.create_fade_animation()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None

    def update(self, time_delta: float) -> None:
        self.animations.update(time_delta)

    @abstractmethod
    def create_fade_animation(self) -> None:
        pass

    def draw(self, surface: pygame.surface.Surface) -> None:
        # Cover the screen with our faded surface
        surface.blit(self.transition_surface, (0, 0))


class FadeOutTransition(FadeTransitionBase):
    def create_fade_animation(self) -> None:
        self.animate(
            self.transition_surface,
            set_alpha=255,
            initial=0,
            duration=self.fade_duration,
        )

    def shutdown(self) -> None:
        if self.client.current_music.previous_song:
            self.client.current_music.play(
                self.client.current_music.previous_song
            )
            self.client.current_music.previous_song = None
        self.client.pop_state(self.caller)


class FadeInTransition(FadeTransitionBase):
    def create_fade_animation(self) -> None:
        self.animate(
            self.transition_surface,
            set_alpha=0,
            initial=255,
            duration=self.fade_duration,
        )
