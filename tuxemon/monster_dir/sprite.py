# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import graphics, prepare, tools
from tuxemon.db import (
    MonsterFlairItemModel,
)
from tuxemon.sprite import Sprite

if TYPE_CHECKING:
    from pygame.surface import Surface


logger = logging.getLogger(__name__)


class SpriteLoader:
    def __init__(self) -> None:
        self.sprite_cache: dict[str, Surface] = {}
        self.animated_sprite_cache: dict[str, Sprite] = {}

    def resolve_path(self, sprite: str) -> str:
        try:
            path = f"{sprite}.png" if not sprite.endswith(".png") else sprite
            full_path = tools.transform_resource_filename(path)
            if full_path:
                return full_path
        except OSError:
            pass
        logger.error(f"Could not find sprite {sprite}")
        return prepare.MISSING_IMAGE

    def load(self, path: str, **kwargs: Any) -> Surface:
        """Loads the monster's sprite images as Pygame surfaces."""
        if path not in self.sprite_cache:
            self.sprite_cache[path] = graphics.load_sprite(
                path, **kwargs
            ).image
        return self.sprite_cache[path]

    def load_animated(
        self, paths: list[str], frame_duration: float, scale: float
    ) -> Sprite:
        resolved = [self.resolve_path(p) for p in paths]
        key = f"{'-'.join(resolved)}:{frame_duration}"
        if key not in self.animated_sprite_cache:
            sprite = graphics.load_animated_sprite(
                resolved, frame_duration, scale
            )
            self.animated_sprite_cache[key] = sprite
        return self.animated_sprite_cache[key]

    def load_and_scale(self, path: str, scale: float) -> Surface:
        cache_key = f"{path}:scale:{scale}"
        if cache_key not in self.sprite_cache:
            base_image = graphics.load_and_scale(path, scale)
            self.sprite_cache[cache_key] = base_image
        return self.sprite_cache[cache_key]


class Flair:
    def __init__(self, category: str, name: str) -> None:
        self.category = category
        self.name = name


class FlairApplier:
    @staticmethod
    def create(flairs: Sequence[MonsterFlairItemModel]) -> dict[str, Flair]:
        _flairs: dict[str, Flair] = {}
        for flair in flairs:
            if flair.names:
                new_flair = Flair(category=flair.category, name=flair.names[0])
                _flairs[new_flair.category] = new_flair
        return _flairs

    @staticmethod
    def apply(
        image: Surface,
        flairs: dict[str, Flair],
        slug: str,
        sprite_type: str,
        loader: SpriteLoader,
        **kwargs: Any,
    ) -> Surface:
        for flair in flairs.values():
            path = loader.resolve_path(
                f"gfx/sprites/battle/{slug}-{sprite_type}-{flair.name}"
            )
            if path != prepare.MISSING_IMAGE:
                flair_surface = loader.load(path, **kwargs)
                image.blit(flair_surface, (0, 0))
        return image


class MonsterSpriteHandler:
    """Manages the loading, caching, and retrieval of monster sprites."""

    def __init__(
        self,
        slug: str = "",
        front_path: str = "",
        back_path: str = "",
        menu1_path: str = "",
        menu2_path: str = "",
        flairs: Optional[dict[str, Flair]] = None,
    ):
        self.loader = SpriteLoader()
        self.slug = slug
        self.front_path = front_path
        self.back_path = back_path
        self.menu1_path = menu1_path
        self.menu2_path = menu2_path
        self.flairs = flairs.copy() if flairs else {}

    def get_sprite(
        self,
        sprite_type: str,
        frame_duration: float = 0.25,
        scale: float = prepare.SCALE,
        **kwargs: Any,
    ) -> Sprite:
        """Returns a Sprite object, applying flairs if necessary."""
        if sprite_type == "front":
            sprite_path = self.front_path
        elif sprite_type == "back":
            sprite_path = self.back_path
        elif sprite_type == "menu01":
            sprite_path = self.menu1_path
        elif sprite_type == "menu02":
            sprite_path = self.menu2_path
        elif sprite_type == "menu":
            return self.loader.load_animated(
                [self.menu1_path, self.menu2_path], frame_duration, scale
            )
        else:
            raise ValueError(f"Cannot find sprite for: {sprite_type}")

        image = self.loader.load(sprite_path, **kwargs)

        if self.flairs:
            image = FlairApplier.apply(
                image,
                self.flairs,
                self.slug,
                sprite_type,
                self.loader,
                **kwargs,
            )

        return Sprite(image=image)

    def load_sprites(self, scale: float = prepare.SCALE) -> dict[str, Surface]:
        """Loads all monster sprites and caches them."""
        sprite_paths = {
            "front": self.front_path,
            "back": self.back_path,
            "menu01": self.menu1_path,
            "menu02": self.menu2_path,
        }

        return {
            key: self.loader.load_and_scale(path, scale)
            for key, path in sprite_paths.items()
            if path
        }
