# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import load_animation_from_frames
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class PlayMapAnimationAction(EventAction):
    """
    Play a map animation at a given position in the world map.

    Script usage:
        .. code-block::

            play_map_animation <animation_name> <duration> <loop> "player"
            play_map_animation <animation_name> <duration> <loop> <tile_pos_x> <tile_pos_y>

    Script parameters:
        animation_name: The name of the animation stored under
            resources/animations/tileset. For example, an animation called
            "grass" will load frames called "grass.xxx.png".
        duration: The duration of each frame of the animation in seconds.
        loop: Can be either "loop" or "noloop" to loop the animation.
        tile_pos: Can be either an x,y coordinate or "player" to draw the
            animation at the player's location.

    """

    name = "play_map_animation"
    animation_name: str
    duration: float
    loop: str
    tile_pos_x: Union[int, str]
    tile_pos_y: Union[int, None] = None

    def start(self) -> None:
        # ('play_animation', 'grass,1.5,noloop,player', '1', 6)
        # "position" can be either a (x, y) tile coordinate or "player"
        animation_name = self.animation_name
        directory = prepare.fetch("animations", "tileset")

        if self.loop == "loop":
            loop = True
        elif self.loop == "noloop":
            loop = False
        else:
            raise ValueError('animation loop value must be "loop" or "noloop"')

        # Check to see if this animation has already been loaded.
        # If it has, play the animation.
        world_state = self.session.client.get_state_by_name(WorldState)

        # Determine the tile position where to draw the animation.
        # TODO: unify npc/player sprites and map animations
        if self.tile_pos_x == "player":
            position = self.session.player.tile_pos
        else:
            assert self.tile_pos_y
            position = (
                int(self.tile_pos_x),
                int(self.tile_pos_y),
            )

        animations = world_state.map_animations
        if animation_name in animations:
            animations[animation_name]["position"] = position
            animations[animation_name]["animation"].play()

        else:
            # Not loaded already, so load it...
            animation = load_animation_from_frames(
                directory,
                animation_name,
                self.duration,
                loop,
            )

            animations[animation_name] = {
                "animation": animation,
                "position": position,
                "layer": 4,
            }

            animation.play()
