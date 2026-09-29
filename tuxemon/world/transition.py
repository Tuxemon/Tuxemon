# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon.graphics import ColorLike

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.movement import MovementManager
    from tuxemon.states.world_state import WorldState


class WorldTransition:
    def __init__(
        self,
        world: WorldState,
        movement: MovementManager,
        resolution: tuple[int, int],
    ) -> None:
        self.world = world
        self.movement = movement
        self.resolution = resolution
        self.transition_alpha: int = 0
        self.transition_surface: Surface | None = None
        self.in_transition: bool = False

    def set_transition_surface(self, color: ColorLike) -> None:
        if (
            self.transition_surface
            and self.transition_surface.get_at((0, 0)) == color
        ):
            return

        new_surface = Surface(self.resolution, SRCALPHA)
        new_surface.fill(color)
        self.transition_surface = new_surface

    def set_transition_state(self, in_transition: bool) -> None:
        """Update the transition state."""
        self.in_transition = in_transition

    def fade_out(
        self,
        duration: float,
        color: ColorLike,
        character: NPC | None = None,
    ) -> None:
        self.set_transition_surface(color)
        self.world.animate(
            self,
            transition_alpha=255,
            initial=0,
            duration=duration,
            round_values=True,
        )
        self.lock_character_controls(character)
        self.set_transition_state(True)

    def fade_in(
        self,
        duration: float,
        color: ColorLike,
        character: NPC | None = None,
    ) -> None:
        self.set_transition_surface(color)
        self.world.animate(
            self,
            transition_alpha=0,
            initial=255,
            duration=duration,
            round_values=True,
        )

        def cleanup() -> None:
            self.set_transition_state(False)
            if character:
                self.movement.unlock_controls(character)

        self.world.task(cleanup, interval=max(duration, 0))

    def fade_and_teleport(
        self,
        duration: float,
        color: ColorLike,
        character: NPC,
        teleport_function: Callable[[], None],
    ) -> None:
        def fade_in() -> None:
            self.fade_in(duration, color, character)

        self.fade_out(duration, color, character)
        task = self.world.task(teleport_function, interval=duration)
        task.chain(fade_in, duration + 0.5)

    def draw(self, surface: Surface) -> None:
        if self.in_transition:
            assert self.transition_surface
            self.transition_surface.set_alpha(self.transition_alpha)
            if self.transition_alpha > 0:
                surface.blit(self.transition_surface, (0, 0))

    def lock_character_controls(self, character: NPC | None) -> None:
        if character:
            self.movement.stop_char(character)
            self.movement.lock_controls(character)

    def unlock_character_controls(
        self, character: NPC | None, delay: float = 0.0
    ) -> None:
        if character:
            self.world.task(
                lambda: self.movement.unlock_controls(character),
                interval=max(delay, 0),
            )
