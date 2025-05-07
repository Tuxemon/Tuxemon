# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.animation_entity import setup_and_play_animation
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class PlayTileAnimationAction(EventAction):
    """
    Trigger a map animation at a specified tile position on the world map.

    Script usage:
        .. code-block::

            play_tile_animation <tile_pos_x>,<tile_pos_y>,<animation_name>,<duration>,<loop>

    Script parameters:
        tile_pos_x, tile_pos_y: Coordinates (x, y) specifying the tile position
            where the animation will be drawn on the map.
        animation_name: The name of the animation stored in the
            resources/animations/tileset directory. For example, an animation
            named "grass" will load frames named "grass_xx.png".
        frame_duration: Duration (in seconds) for each frame of the animation.
        loop_mode: Indicates whether the animation should loop. Options: "loop"
            or "noloop".
    """

    name = "play_tile_animation"
    tile_pos_x: int
    tile_pos_y: int
    animation_name: str
    duration: float
    loop: str

    def start(self) -> None:
        world_state = self.session.client.get_state_by_name(WorldState)
        position = (self.tile_pos_x, self.tile_pos_y)
        animations = world_state.map_renderer.map_animations

        setup_and_play_animation(
            animation_name=self.animation_name,
            duration=self.duration,
            loop=self.loop,
            position=position,
            animations=animations,
            layer=4,
        )
