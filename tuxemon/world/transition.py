# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon.graphics import ColorLike

if TYPE_CHECKING:
    from tuxemon.movement import MovementManager
    from tuxemon.npc import NPC
    from tuxemon.states.world.worldstate import WorldState


class WorldTransition:
    def __init__(self, world: WorldState, movement: MovementManager) -> None:
        self.world = world
        self.movement = movement
        self.transition_alpha = 0
        self.transition_surface: Optional[Surface] = None
        self.in_transition = False

    def set_transition_surface(self, color: ColorLike) -> None:
        if (
            self.transition_surface
            and self.transition_surface.get_at((0, 0)) == color
        ):
            return

        new_surface = Surface(self.world.client.screen.get_size(), SRCALPHA)
        new_surface.fill(color)
        self.transition_surface = new_surface

    def set_transition_state(self, in_transition: bool) -> None:
        """Update the transition state."""
        self.in_transition = in_transition

    def fade_out(
        self,
        duration: float,
        color: ColorLike,
        character: Optional[NPC] = None,
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
        character: Optional[NPC] = None,
    ) -> None:
        self.set_transition_surface(color)
        self.world.animate(
            self,
            transition_alpha=0,
            initial=255,
            duration=duration,
            round_values=True,
        )
        self.unlock_character_controls(character, duration)

        def cleanup() -> None:
            self.set_transition_state(False)

        self.world.task(cleanup, interval=duration)

    def fade_and_teleport(
        self,
        duration: float,
        color: ColorLike,
        character: NPC,
        teleport_function: Callable[[], None],
    ) -> None:
        def fade_in() -> None:
            self.fade_in(duration, color, character)

        self.movement.lock_controls(character)
        self.world.remove_animations_of(self.world)
        self.world.stop_scheduled_callbacks()
        self.movement.stop_and_reset_char(character)

        self.fade_out(duration, color, character)
        task = self.world.task(teleport_function, interval=duration)
        task.chain(fade_in, duration + 0.5)

    def draw(self, surface: Surface) -> None:
        if self.in_transition:
            assert self.transition_surface
            self.transition_surface.set_alpha(self.transition_alpha)
            if self.transition_alpha > 0:
                surface.blit(self.transition_surface, (0, 0))

    def lock_character_controls(self, character: Optional[NPC]) -> None:
        if character:
            self.movement.stop_char(character)
            self.movement.lock_controls(character)

    def unlock_character_controls(
        self, character: Optional[NPC], duration: float
    ) -> None:
        if character:
            self.world.task(
                lambda: self.movement.unlock_controls(character),
                interval=max(duration, 0),
            )
