# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable

from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.db import AnimationModel, db
from tuxemon.graphics import create_animation, load_frames_files
from tuxemon.map_view import AnimationInfo

logger = logging.getLogger(__name__)


class AnimationEntity:
    """Holds all the values for animations."""

    def __init__(
        self,
        slug: str,
        duration: float = prepare.FRAME_TIME,
        loop: bool = False,
    ) -> None:
        self.slug: str = ""
        self.duration: float = duration
        self.loop: bool = loop
        self.file: str = ""
        self.directory: str = ""
        self.frames: Iterable[Surface] = []
        self.load(slug)

    def load(self, slug: str) -> None:
        """Loads animation."""
        results = AnimationModel.lookup(slug, db)
        self.slug = results.slug
        self.file = results.file

        self.directory = prepare.fetch("animations", self.file)
        self.frames = load_frames_files(self.directory, self.slug)
        self.play = create_animation(self.frames, self.duration, self.loop)


def setup_and_play_animation(
    animation_name: str,
    duration: float,
    loop: str,
    position: tuple[int, int],
    animations: dict[str, AnimationInfo],
    layer: int,
) -> None:
    """
    Sets up and plays a map animation with configurable layering.

    Parameters:
        animation_name: The name of the animation to play.
        duration: Duration (in seconds) for each frame of the animation.
        loop: Indicates whether the animation should loop. Must be "loop"
            or "noloop".
        position: The (x, y) coordinates where the animation should be
            displayed.
        animations: A dictionary of existing animations, storing their
            states and properties.
        layer: The rendering layer for the animation, affecting its visual
            depth.

    Raises:
        ValueError: If `loop` is not "loop" or "noloop".
    """
    if loop == "loop":
        loop_mode = True
    elif loop == "noloop":
        loop_mode = False
    else:
        raise ValueError(f"{loop} value must be 'loop' or 'noloop'")

    _animation = AnimationEntity(animation_name, duration, loop_mode)

    if animation_name in animations:
        logger.debug(f"{animation_name} loaded")
        animations[animation_name].position = position
        animations[animation_name].animation.play()
    else:
        logger.debug(f"{animation_name} not loaded, loading")
        animations[animation_name] = AnimationInfo(
            _animation.play, position, layer
        )
        _animation.play.play()
