# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event import get_npc
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

            play_map_animation <animation_name> <duration> <loop> "npc_slug"
            play_map_animation <animation_name> <duration> <loop> <tile_pos_x> <tile_pos_y>

    Script parameters:
        animation_name: The name of the animation stored under
            resources/animations/tileset. For example, an animation called
            "grass" will load frames called "grass.xxx.png".
        duration: The duration of each frame of the animation in seconds.
        loop: Can be either "loop" or "noloop" to loop the animation.
        tile_pos: Can be either an x,y coordinate or "npc_slug" to draw the
            animation at the character's location.

    """

    name = "play_map_animation"
    animation_name: str
    duration: float
    loop: str
    tile_pos_x: str
    tile_pos_y: Optional[int] = None

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

        world_state = self.session.client.get_state_by_name(WorldState)

        # Determine the tile position where to draw the animation.
        # TODO: unify npc/player sprites and map animations
        if not self.tile_pos_x.isdigit():
            character = get_npc(self.session, self.tile_pos_x)
            if character is None:
                logger.error(f"{self.tile_pos_x} not found")
                return
            position = character.tile_pos
        else:
            if self.tile_pos_y is None:
                logger.error("Y coordinate is missing.")
                return
            position = ((int(self.tile_pos_x)), (self.tile_pos_y))

        animations = world_state.map_animations
        if animation_name in animations:
            logger.debug(f"{animation_name} loaded")
            animations[animation_name]["position"] = position
            animations[animation_name]["animation"].play()
        else:
            logger.debug(f"{animation_name} not loaded, loading")
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
