# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.animation_entity import setup_and_play_animation
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class PlayMapAnimationAction(EventAction):
    """
    Trigger a map animation at a specified position based on the character's
    coordinates within the world map

    Script usage:
        .. code-block::

            play_map_animation <animation_name>,<duration>,<loop>,<character>

    Script parameters:
        animation_name: The name of the animation stored in the
            resources/animations/tileset directory. For example, an animation
            named "grass" will load frames named "grass_xx.png".
        frame_duration: Duration (in seconds) for each frame of the animation.
        loop_mode: Indicates whether the animation should loop. Options: "loop"
            or "noloop".
        character: Either "player" or character slug name (e.g. "npc_maple").
    """

    name = "play_map_animation"
    animation_name: str
    duration: float
    loop: str
    character: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return

        world_state = self.session.client.get_state_by_name(WorldState)
        position = character.tile_pos
        animations = world_state.map_renderer.map_animations

        setup_and_play_animation(
            animation_name=self.animation_name,
            duration=self.duration,
            loop=self.loop,
            position=position,
            animations=animations,
            layer=4,
        )
