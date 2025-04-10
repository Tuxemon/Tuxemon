# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

import pygame

from tuxemon.graphics import ColorLike

if TYPE_CHECKING:
    from tuxemon.states.world.worldstate import WorldState


class WorldTransition:
    def __init__(self, world: WorldState) -> None:
        self.world = world
        self.transition_alpha = 0
        self.transition_surface: Optional[pygame.surface.Surface] = None
        self.in_transition = False

    def set_transition_surface(self, color: ColorLike) -> None:
        self.transition_surface = pygame.Surface(
            self.world.client.screen.get_size(), pygame.SRCALPHA
        )
        self.transition_surface.fill(color)

    def set_transition_state(self, in_transition: bool) -> None:
        """Update the transition state."""
        self.in_transition = in_transition

    def fade_out(self, duration: float, color: ColorLike) -> None:
        self.set_transition_surface(color)
        self.world.animate(
            self,
            transition_alpha=255,
            initial=0,
            duration=duration,
            round_values=True,
        )
        self.world.stop_char(self.world.player)
        self.world.lock_controls(self.world.player)
        self.set_transition_state(True)

    def fade_in(self, duration: float, color: ColorLike) -> None:
        self.set_transition_surface(color)
        self.world.animate(
            self,
            transition_alpha=0,
            initial=255,
            duration=duration,
            round_values=True,
        )
        self.world.task(
            lambda: self.world.unlock_controls(self.world.player),
            max(duration, 0),
        )

        def cleanup() -> None:
            self.set_transition_state(False)

        self.world.task(cleanup, duration)

    def fade_and_teleport(
        self,
        duration: float,
        color: ColorLike,
        teleport_function: Callable[[], None],
    ) -> None:
        def fade_in() -> None:
            self.fade_in(duration, color)

        self.world.lock_controls(self.world.player)
        self.world.remove_animations_of(self.world)
        self.world.remove_animations_of(self.set_transition_state)
        self.world.stop_and_reset_char(self.world.player)

        self.fade_out(duration, color)
        task = self.world.task(teleport_function, duration)
        task.chain(fade_in, duration + 0.5)

    def draw(self, surface: pygame.surface.Surface) -> None:
        if self.in_transition:
            assert self.transition_surface
            self.transition_surface.set_alpha(self.transition_alpha)
            surface.blit(self.transition_surface, (0, 0))
