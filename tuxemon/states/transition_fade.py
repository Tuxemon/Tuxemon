# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon.graphics import ColorLike
from tuxemon.platform.const.graphics import BLACK_COLOR
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class FadeTransitionBase(State):
    """The state responsible for the battle transitions."""

    name: ClassVar[str] = "FadeTransitionBase"
    force_draw = True
    state_duration = 1.0
    fade_duration = 1.5

    def __init__(
        self,
        client: BaseClient,
        state_duration: float | None = None,
        fade_duration: float | None = None,
        caller: State | None = None,
        color: ColorLike = BLACK_COLOR,
        **kwargs: Any,
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
        super().__init__(client=client, **kwargs)

        logger.debug("Initializing fade transition")

        if state_duration is not None:
            self.state_duration = state_duration

        if fade_duration is not None:
            self.fade_duration = fade_duration

        self.caller = caller
        resolution = self.client.context.resolution
        self.transition_surface = Surface(resolution, SRCALPHA)
        self.transition_surface.fill(color)
        self.task(self.client.pop_state, interval=self.state_duration)
        self.create_fade_animation()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None

    def update(self, dt: float) -> None:
        self.animations.update(dt)

    @abstractmethod
    def create_fade_animation(self) -> None:
        pass

    def draw(self, surface: Surface) -> None:
        # Cover the screen with our faded surface
        surface.blit(self.transition_surface, (0, 0))


class FadeOutTransition(FadeTransitionBase):
    name: ClassVar[str] = "FadeOutTransition"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

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
    name: ClassVar[str] = "FadeInTransition"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def create_fade_animation(self) -> None:
        self.animate(
            self.transition_surface,
            set_alpha=0,
            initial=255,
            duration=self.fade_duration,
        )
