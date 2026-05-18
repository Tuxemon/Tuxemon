# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.database.runtime import db
from tuxemon.db import AnimationModel, LoopMode
from tuxemon.graphics import create_animation, slice_spritesheet
from tuxemon.sprite import Sprite
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.surfanim import SurfaceAnimation

logger = logging.getLogger(__name__)


@dataclass
class AnimationInfo:
    animation: SurfaceAnimation
    position: tuple[int, int]
    layer: int
    visible: bool = True

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False


class AnimationManager:
    """Manages the creation, caching, and playback of animations."""

    def __init__(self) -> None:
        self._cache: dict[str, AnimationInfo] = {}

    def show(self, slug: str) -> None:
        info = self._cache.get(slug)
        if info:
            info.show()

    def hide(self, slug: str) -> None:
        info = self._cache.get(slug)
        if info:
            info.hide()

    def setup_and_play(
        self,
        slug: str,
        duration: float,
        loop: LoopMode,
        position: tuple[int, int],
        layer: int,
    ) -> SurfaceAnimation:
        """Creates (or retrieves) an animation, updates its position/layer, and starts playback."""
        self.get_or_create_animation(slug, duration=duration, loop=loop)

        info = self._cache[slug]
        info.position = position
        info.layer = layer
        info.animation.play()

        logger.debug(
            f"Setup and playing animation '{slug}' at {position} on layer {layer}"
        )
        return info.animation

    def get_or_create_animation(
        self,
        slug: str,
        *,
        duration: float | None = None,
        loop: LoopMode | int,
    ) -> SurfaceAnimation:
        """Retrieves a cached animation or creates a new one."""
        if slug in self._cache:
            return self._cache[slug].animation

        data = AnimationModel.lookup(slug, db)

        sheet_path = fetch_asset("animations", f"{data.file}/{data.slug}.png")
        frames = slice_spritesheet(sheet_path, data.frame_x, data.frame_y)

        if duration is None:
            duration = data.duration

        assert duration is not None, "Animation duration must be set"

        loop_value = loop.value if isinstance(loop, LoopMode) else loop

        surface_animation = create_animation(frames, duration, loop_value)
        surface_animation.rate = data.rate
        surface_animation.flip(data.flip_axes)

        self._cache[slug] = AnimationInfo(surface_animation, (0, 0), 0)

        logger.debug(f"Created and cached animation '{slug}'")
        return surface_animation

    def get_sprite(
        self,
        slug: str,
        loop: LoopMode | int,
        flip_axes: FlipAxes | None = None,
    ) -> Sprite:
        """
        Returns a Sprite with a unique animation instance.
        """
        template = self.get_or_create_animation(slug=slug, loop=loop)
        animation_instance = template.copy()

        if flip_axes is not None:
            animation_instance.flip(flip_axes)

        animation_instance.play()
        return Sprite(animation=animation_instance)

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
