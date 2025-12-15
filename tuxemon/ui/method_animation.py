# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from tuxemon.animation_entity import AnimationManager
from tuxemon.sprite import Sprite
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.status.status import Status


@dataclass(frozen=True)
class MethodKey:
    slug: str
    flipped: bool


class MethodAnimationCache:
    """
    Caches and retrieves sprites for techniques, statuses, and items
    used as animated methods in gameplay.
    """

    def __init__(self, manager: AnimationManager) -> None:
        self._manager = manager
        self._sprites: dict[MethodKey, Optional[Sprite]] = {}

    def get(
        self, method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Retrieves a cached sprite for the given method, creating it if necessary.

        Parameters:
            method: A Technique, Status, or Item instance.
            is_flipped: Whether the animation should be flipped.

        Returns:
            A Sprite object representing the method's animation, or None if unavailable.
        """
        if not method.visuals.animation:
            return None

        key = MethodKey(method.visuals.animation, is_flipped)

        if key not in self._sprites:
            self._sprites[key] = self._load_sprite(method, is_flipped)

        return self._sprites[key]

    def _load_sprite(
        self, method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Loads and prepares a sprite for the given method.

        Parameters:
            method: The method whose animation should be loaded.
            is_flipped: Whether to apply flipping to the animation.

        Returns:
            A Sprite object or None if the method has no animation.
        """

        if not method.visuals.animation:
            return None

        animation = self._manager.get_or_create_animation(
            slug=method.visuals.animation,
            loop=method.visuals.loop,
        )

        if is_flipped:
            animation.flip(method.visuals.flip_axes)

        animation.play()
        return Sprite(animation=animation)
