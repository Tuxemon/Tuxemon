# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pygame.surface import Surface

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.db import AnimationModel, db
from tuxemon.graphics import create_animation, load_frames_files
from tuxemon.map.map_view import AnimationInfo

if TYPE_CHECKING:
    from tuxemon.surfanim import SurfaceAnimation

logger = logging.getLogger(__name__)


class AnimationEntity:
    """Holds all the values for animations."""

    def __init__(
        self,
        slug: str,
        duration: Optional[float] = None,
        loop: Optional[int] = None,
    ) -> None:
        self.slug = slug
        self.duration = duration
        self.loop = loop
        self.file: str = ""
        self.frames: list[Surface] = []
        self._load_data()

    def _load_data(self) -> None:
        """Loads animation."""
        results = AnimationModel.lookup(self.slug, db)
        self.slug = results.slug
        self.file = results.file
        self.duration = (
            self.duration if self.duration is not None else results.duration
        )
        self.loop = self.loop if self.loop is not None else results.loop

        directory = fetch_asset("animations", self.file)
        self.frames = list(load_frames_files(directory, self.slug))


class AnimationManager:
    """Manages the creation, caching, and playback of animations."""

    def __init__(self) -> None:
        self._cache: dict[str, AnimationInfo] = {}

    def get_or_create_animation(
        self,
        slug: str,
        duration: Optional[float] = None,
        loop: Optional[int] = None,
    ) -> SurfaceAnimation:
        """
        Retrieves a cached animation or creates a new one.
        """
        if slug in self._cache:
            return self._cache[slug].animation

        entity = AnimationEntity(slug, duration, loop)

        assert entity.duration is not None, "Animation duration must be set"
        assert entity.loop is not None, "Animation loop mode must be set"

        surface_animation = create_animation(
            entity.frames, entity.duration, entity.loop
        )

        results = AnimationModel.lookup(slug, db)
        surface_animation.rate = results.rate
        surface_animation.flip(results.flip_axes)

        self._cache[slug] = AnimationInfo(surface_animation, (0, 0), 0)

        logger.debug(f"Created and cached animation '{slug}'")
        return surface_animation

    def play_animation(
        self, animation_name: str, position: tuple[int, int], layer: int
    ) -> None:
        """Plays a cached animation and sets its position and layer."""
        animation_info = self._cache.get(animation_name)
        if animation_info:
            animation_info.position = position
            animation_info.layer = layer
            animation_info.animation.play()
            logger.debug(f"Playing existing animation: {animation_name}")
        else:
            logger.warning(
                f"Attempted to play non-existent animation: {animation_name}"
            )

    def update_all(self, time_delta: float) -> None:
        """Updates all animations in the cache."""
        for anim_info in self._cache.values():
            anim_info.animation.update(time_delta)


def setup_and_play_animation(
    animation_name: str,
    duration: float,
    loop: str,
    position: tuple[int, int],
    animations: dict[str, AnimationInfo],
    layer: int,
) -> None:
    """
    Sets up and plays a map animation using AnimationManager.

    Parameters:
        animation_name: The name of the animation to play.
        duration: Duration (in seconds) for each frame of the animation.
        loop: "loop" or "noloop" to control animation looping.
        position: (x, y) coordinates for display.
        animations: Dictionary of existing animations.
        layer: Rendering layer.
        manager: Instance of AnimationManager to manage caching and playback.
    """
    if loop == "loop":
        loop_mode = -1
    elif loop == "noloop":
        loop_mode = 0
    else:
        raise ValueError(f"{loop} value must be 'loop' or 'noloop'")

    manager = AnimationManager()
    animation = manager.get_or_create_animation(
        animation_name, duration, loop_mode
    )

    if animation_name in animations:
        logger.debug(f"{animation_name} already loaded")
        animations[animation_name].position = position
        animations[animation_name].animation.play()
    else:
        logger.debug(f"{animation_name} not loaded, creating new")
        animations[animation_name] = AnimationInfo(animation, position, layer)
        animation.play()
