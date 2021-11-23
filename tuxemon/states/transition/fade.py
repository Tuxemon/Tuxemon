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
# states.FadeTransitionBase
# states.FadeOutTransition
# states.FadeInTransition
#
from __future__ import annotations
import logging
from abc import abstractmethod

import pygame

from tuxemon.state import State
from typing import Any, Optional
from tuxemon.platform.events import PlayerInput
from tuxemon.graphics import ColorLike

logger = logging.getLogger(__name__)


class FadeTransitionBase(State):
    """The state responsible for the battle transitions."""

    force_draw = True
    state_duration = 1.0
    fade_duration = 1.5
    color: ColorLike = (0, 0, 0)

    def startup(
        self,
        *,
        state_duration: Optional[float] = None,
        fade_duration: Optional[float] = None,
        caller: Optional[State] = None,
        **kwargs: Any,
    ) -> None:
        logger.debug("Initializing fade transition")

        if state_duration is not None:
            self.state_duration = state_duration

        if fade_duration is not None:
            self.fade_duration = fade_duration

        self.caller = caller
        size = self.client.screen.get_size()
        self.transition_surface = pygame.Surface(size)
        self.transition_surface.fill(self.color)
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
        if self.client.current_music["previoussong"]:
            self.client.event_engine.execute_action(
                "play_music",
                [self.client.current_music["previoussong"]],
            )
            self.client.current_music["previoussong"] = None
        self.client.pop_state(self.caller)


class FadeInTransition(FadeTransitionBase):
    def create_fade_animation(self) -> None:
        self.animate(
            self.transition_surface,
            set_alpha=0,
            initial=255,
            duration=self.fade_duration,
        )
