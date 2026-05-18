# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tuxemon.map.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.entity.path.controller import PathController

logger = logging.getLogger(__name__)


class BehaviorPolicy:
    """
    Decides high-level NPC behavior.
    Called once per update() before movement.
    """

    def update(self, npc: NPC, controller: PathController, dt: float) -> None:
        pass


class PatrolBehavior(BehaviorPolicy):
    def __init__(self, route: Sequence[tuple[int, int]]):
        self.route = route
        self.index = 0

    def update(self, npc: NPC, controller: PathController, dt: float) -> None:

        # Skip if dialog or menu is open
        if any(
            state_name in ("WorldMenuState", "DialogState", "ChoiceState")
            for state_name in npc.session.client.active_state_names
        ):
            return

        # Skip if player is looking at the NPC
        player = npc.session.player
        client = npc.session.client

        tiles_in_front = get_coords(
            player.tile_pos, client.map_manager.map_size
        )
        direction = get_direction(player.tile_pos, npc.tile_pos)

        if npc.tile_pos in tiles_in_front and player.facing == direction:
            return

        if player.tile_pos == self.route[self.index]:
            return

        if not controller.path and not controller.pathfinding:
            next_tile = self.route[self.index]
            controller.start_path(next_tile)
            self.index = (self.index + 1) % len(self.route)


class WanderBehavior(BehaviorPolicy):
    def __init__(
        self,
        bounds: Sequence[tuple[int, int]] | None = None,
        frequency: float = 1.0,
    ):
        self.bounds = bounds
        self.frequency = frequency
        self.timer = 0.0

    def update(self, npc: NPC, controller: PathController, dt: float) -> None:
        # Decrement timer
        self.timer -= dt
        if self.timer > 0:
            return

        # Reset timer
        self.timer = self.frequency

        # Skip if already moving
        if controller.path or npc.moving:
            return

        # Skip if dialog or menu is open
        if any(
            state_name in ("WorldMenuState", "DialogState", "ChoiceState")
            for state_name in npc.session.client.active_state_names
        ):
            return

        # Skip if player is looking at the NPC
        player = npc.session.player
        client = npc.session.client

        tiles_in_front = get_coords(
            player.tile_pos, client.map_manager.map_size
        )
        direction = get_direction(player.tile_pos, npc.tile_pos)

        if npc.tile_pos in tiles_in_front and player.facing == direction:
            return

        # Get exits
        origin = npc.tile_pos
        exits = npc.client.pathfinder.get_exits(origin, npc.facing)
        if not exits:
            return

        # Apply bounds if provided
        if self.bounds:
            exits = [p for p in exits if p in self.bounds]
            if not exits:
                return

        # Pick a random exit
        controller.start_path(random.choice(exits))
