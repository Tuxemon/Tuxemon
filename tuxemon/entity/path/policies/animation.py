# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.db import Direction
from tuxemon.map.map import get_direction

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC


logger = logging.getLogger(__name__)


class MovementAnimationPolicy:
    """
    Handles animation logic for NPC movement.
    """

    def on_step(self, npc: NPC, direction: Direction) -> None:
        npc.sprite_controller.play_animation(direction)

    def on_face(self, npc: NPC, direction: Direction) -> None:
        npc.set_facing(direction)

    def on_stop(self, npc: NPC) -> None:
        npc.sprite_controller.stop_animation()

    def compute_facing(self, npc: NPC, target: tuple[int, int]) -> Direction:
        return get_direction(npc.position, target)
