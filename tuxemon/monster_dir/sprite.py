# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Optional

from pygame.surface import Surface

from tuxemon import graphics, prepare, tools
from tuxemon.db import ColorModel, FlairModel, db
from tuxemon.sprite import Sprite

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
    def __init__(
        self,
        category: str,
        slug: str,
        weight: float = 1.0,
        layer: int = 0,
        layer_order: int = 0,
        x_offset: int = 0,
        y_offset: int = 0,
        sprite_type_override: Optional[str] = None,
        sprite_type: Optional[set[str]] = None,
        color: Optional[ColorModel] = None,
    ) -> None:
        self.category = category
        self.slug = slug
        self.weight = weight
        self.layer = layer
        self.layer_order = layer_order
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.sprite_type_override = sprite_type_override
        self.sprite_type = sprite_type
        self.color = color

    def get_state(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "slug": self.slug,
            "weight": self.weight,
            "layer": self.layer,
            "layer_order": self.layer_order,
            "x_offset": self.x_offset,
            "y_offset": self.y_offset,
            "sprite_type_override": self.sprite_type_override,
            "sprite_type": (
                list(self.sprite_type) if self.sprite_type else None
            ),
            "color": (
                {
                    "red": self.color.red,
                    "green": self.color.green,
                    "blue": self.color.blue,
                    "alpha": self.color.alpha,
                }
                if self.color
                else None
            ),
        }

    @classmethod
    def from_state(cls, data: dict[str, Any]) -> Flair:
        color_data = data.get("color")
        color = ColorModel(**color_data) if color_data else None
        return cls(
            category=data["category"],
            slug=data["slug"],
            weight=data.get("weight", 1.0),
            layer=data.get("layer", 0),
            layer_order=data.get("layer_order", 0),
            x_offset=data.get("x_offset", 0),
            y_offset=data.get("y_offset", 0),
            sprite_type_override=data.get("sprite_type_override"),
            sprite_type=set(data.get("sprite_type", [])),
            color=color,
        )

    def __lt__(self, other: Flair) -> bool:
        return (self.layer, self.layer_order) < (
            other.layer,
            other.layer_order,
        )

    def __repr__(self) -> str:
        parts = [
            f"[{self.category}] {self.slug}",
            f"Layer {self.layer}",
            f"Order {self.layer_order}",
        ]
        if self.sprite_type:
            parts.append(f"Types: {','.join(sorted(self.sprite_type))}")
        if self.color:
            parts.append(
                f"Tint: ({self.color.red},{self.color.green},{self.color.blue},{self.color.alpha})"
            )
        return f"<Flair {' | '.join(parts)}>"


class FlairSelector:
    @staticmethod
    def select(
        flair_pool: Sequence[FlairModel],
    ) -> dict[str, Flair]:
        selected: dict[str, Flair] = {}
        grouped = group_by_category(flair_pool)

        for category, flairs in grouped.items():
            flair = select_weighted_flair(flairs)
            if flair:
                selected[category] = Flair(
                    category=flair.category,
                    slug=flair.slug,
                    weight=flair.weight,
                    layer=flair.layer,
                    layer_order=flair.layer_order,
                    x_offset=flair.x_offset or 0,
                    y_offset=flair.y_offset or 0,
                    sprite_type_override=flair.sprite_type_override,
                    sprite_type=flair.sprite_type,
                    color=flair.color,
                )
        return selected


class FlairApplier:
    @staticmethod
    def create(flair_slugs: set[str]) -> dict[str, Flair]:
        flair_models = [FlairModel.lookup(slug, db) for slug in flair_slugs]
        return FlairSelector.select(flair_models)

    @staticmethod
    def apply(
        image: Surface,
        flairs: dict[str, Flair],
        sprite_type: str,
        loader: SpriteLoader,
        **kwargs: Any,
    ) -> Surface:
        for flair in sorted(flairs.values()):
            # Skip flair if it's meant for a different sprite type
            if flair.sprite_type and sprite_type not in flair.sprite_type:
                continue

            logger.debug(
                f"Drawing flair: {flair.slug} (Layer {flair.layer}, Order {flair.layer_order})"
            )

            folder = flair.sprite_type_override or flair.category
            path = loader.resolve_path(
                f"gfx/sprites/flairs/{folder}/{flair.slug}"
            )

            if path == prepare.MISSING_IMAGE:
                logger.warning(f"Missing flair image: {flair.slug}")
                continue

            flair_surface = loader.load(path, **kwargs)

            if flair.color:
                flair_surface = apply_color_tint(flair_surface, flair.color)

            image.blit(flair_surface, (flair.x_offset, flair.y_offset))

        return image


def group_by_category(
    flairs: Sequence[FlairModel],
) -> dict[str, list[FlairModel]]:
    grouped: dict[str, list[FlairModel]] = defaultdict(list)
    for flair in flairs:
        grouped[flair.category].append(flair)
    return grouped


def select_weighted_flair(
    flairs: Sequence[FlairModel],
) -> Optional[FlairModel]:
    if not flairs:
        return None

    total_weight = sum(f.weight for f in flairs)
    if total_weight == 0:
        return None

    # Special case: only one flair
    if len(flairs) == 1:
        flair = flairs[0]
        chance = flair.weight / max(total_weight, 1.0)
        if random.random() <= chance:
            return flair
        return None

    # Normal weighted selection
    r = random.uniform(0, total_weight)
    upto = 0.0
    for flair in flairs:
        upto += flair.weight
        if r <= upto:
            return flair
    return None


def apply_color_tint(surface: Surface, color: ColorModel) -> Surface:
    tinted = surface.copy()
    width, height = tinted.get_size()
    for x in range(width):
        for y in range(height):
            r, g, b, a = tinted.get_at((x, y))
            if a == 0:
                continue  # Skip fully transparent pixels

            r = (r * color.red) // 255
            g = (g * color.green) // 255
            b = (b * color.blue) // 255
            a = (a * color.alpha) // 255

            tinted.set_at((x, y), (r, g, b, a))
    return tinted


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
        self._flair_cache: dict[str, Surface] = {}

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

        cache_key = f"{sprite_type}:{hash(frozenset(self.flairs.items()))}"
        if cache_key in self._flair_cache:
            return Sprite(image=self._flair_cache[cache_key])

        image = self.loader.load(sprite_path, **kwargs)

        if self.flairs:
            image = FlairApplier.apply(
                image, self.flairs, sprite_type, self.loader, **kwargs
            )

        self._flair_cache[cache_key] = image
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

    def refresh_flairs(self, new_flairs: dict[str, Flair]) -> None:
        self.flairs = new_flairs.copy()
        self._flair_cache.clear()
