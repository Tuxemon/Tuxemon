# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
    """Caches and retrieves sprites for gameplay methods."""

    def __init__(self, manager: AnimationManager) -> None:
        self._manager = manager
        self._sprites: dict[MethodKey, Sprite | None] = {}

    def get(
        self, method: Technique | Status | Item, is_flipped: bool
    ) -> Sprite | None:
        slug = method.visuals.animation
        if not slug:
            return None

        key = MethodKey(slug, is_flipped)

        if key not in self._sprites:
            self._sprites[key] = self._manager.get_sprite(
                slug=slug,
                loop=method.visuals.loop_mode(),
                flip_axes=method.visuals.flip_axes if is_flipped else None,
            )

        return self._sprites[key]
