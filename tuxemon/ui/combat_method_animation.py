# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from tuxemon.animation_entity import AnimationEntity
from tuxemon.sprite import Sprite
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.status.status import Status


class MethodAnimationCache:
    def __init__(self) -> None:
        self._sprites: dict[
            Union[Technique, Status, Item], Optional[Sprite]
        ] = {}

    def get(
        self, method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return a sprite usable as a method (technique, item, status) animation.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        try:
            return self._sprites[method]
        except KeyError:
            sprite = self.load_method_animation(method, is_flipped)
            self._sprites[method] = sprite
            return sprite

    @staticmethod
    def load_method_animation(
        method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return animated sprite from a technique, status or item.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        if not method.animation:
            return None

        ani = AnimationEntity(method.animation)
        if is_flipped:
            ani.play.flip(method.flip_axes)
        return Sprite(animation=ani.play)
