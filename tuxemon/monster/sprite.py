# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from pygame.surface import Surface

from tuxemon import graphics, tools
from tuxemon.database.runtime import db
from tuxemon.db import ColorModel, FlairModel
from tuxemon.platform.const.graphics import MISSING_IMAGE
from tuxemon.sprite import Sprite

if TYPE_CHECKING:
    from tuxemon.db import MonsterModel

logger = logging.getLogger(__name__)


class SpriteLoader:
    def __init__(self) -> None:
        self.sprite_cache: dict[str, Surface] = {}

    def resolve_path(self, sprite: str) -> str:
        try:
            path = f"{sprite}.png" if not sprite.endswith(".png") else sprite
            full_path = tools.transform_resource_filename(path)
            if full_path:
                return full_path
        except OSError:
            pass
        logger.error(f"Could not find sprite {sprite}")
        return MISSING_IMAGE

    def load(self, path: str, **kwargs: Any) -> Surface:
        """Loads the monster's sprite images as Pygame surfaces."""
        if path not in self.sprite_cache:
            self.sprite_cache[path] = graphics.load_sprite(
                path, **kwargs
            ).image
        return self.sprite_cache[path]

    def load_animated_frames(
        self, frames: list[Surface], frame_duration: float
    ) -> Sprite:
        return graphics.load_animated_frames(frames, frame_duration)

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
        sprite_type_override: str | None = None,
        sprite_type: set[str] | None = None,
        color: ColorModel | None = None,
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

            if path == MISSING_IMAGE:
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
) -> FlairModel | None:
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
    """Manages loading and slicing of a combined monster sprite sheet."""

    def __init__(
        self,
        slug: str,
        sheet_path: str,
        front_rect: tuple[int, int, int, int],
        back_rect: tuple[int, int, int, int],
        menu1_rect: tuple[int, int, int, int],
        menu2_rect: tuple[int, int, int, int],
        flairs: dict[str, Flair] | None = None,
    ):
        self.loader = SpriteLoader()
        self.slug = slug
        self.sheet_path = sheet_path

        self.rects = {
            "front": front_rect,
            "back": back_rect,
            "menu01": menu1_rect,
            "menu02": menu2_rect,
        }

        self.flairs = flairs.copy() if flairs else {}
        self._flair_cache: dict[str, Surface] = {}
        self.sheet = graphics.load_raw_image(self.sheet_path)

    @classmethod
    def from_model(cls, model: MonsterModel) -> MonsterSpriteHandler | None:
        if model.sprites is None:
            return None

        return cls(
            slug=model.slug,
            sheet_path=model.sprites.sheet,
            front_rect=model.sprites.front_rect,
            back_rect=model.sprites.back_rect,
            menu1_rect=model.sprites.menu1_rect,
            menu2_rect=model.sprites.menu2_rect,
        )

    def _slice(self, sprite_type: str) -> Surface:
        """Extracts a subsurface from the sheet."""
        if sprite_type not in self.rects:
            raise ValueError(f"Unknown sprite type: {sprite_type}")

        rect = self.rects[sprite_type]
        return self.sheet.subsurface(rect)

    def get_sprite(
        self,
        sprite_type: str,
        scale: float,
        frame_duration: float = 0.25,
        **kwargs: Any,
    ) -> Sprite:
        """
        Returns a Sprite object from the sheet.
        Handles static sprites and animated menu sprites.
        """
        if sprite_type == "menu":
            frame1 = self._slice("menu01")
            frame2 = self._slice("menu02")

            if scale != 1:
                frame1 = graphics.scale_surface(frame1, scale)
                frame2 = graphics.scale_surface(frame2, scale)

            if self.flairs:
                frame1 = FlairApplier.apply(
                    frame1, self.flairs, "menu01", self.loader, **kwargs
                )
                frame2 = FlairApplier.apply(
                    frame2, self.flairs, "menu02", self.loader, **kwargs
                )

            return self.loader.load_animated_frames(
                [frame1, frame2], frame_duration=frame_duration
            )

        flair_key: frozenset[tuple[str, tuple[tuple[str, Any], ...]]] = (
            frozenset(
                (k, tuple(sorted(v.get_state().items())))
                for k, v in self.flairs.items()
            )
        )
        cache_key = f"{sprite_type}:{hash(flair_key)}:{scale}"
        if cache_key in self._flair_cache:
            return Sprite(image=self._flair_cache[cache_key])

        image = self._slice(sprite_type)

        if scale != 1:
            image = graphics.scale_surface(image, scale)

        if self.flairs:
            image = FlairApplier.apply(
                image, self.flairs, sprite_type, self.loader, **kwargs
            )

        self._flair_cache[cache_key] = image
        return Sprite(image=image)

    def load_sprites(self, scale: float) -> dict[str, Surface]:
        return {
            key: graphics.scale_surface(self._slice(key), scale)
            for key in self.rects
        }

    def refresh_flairs(self, new_flairs: dict[str, Flair]) -> None:
        self.flairs = new_flairs.copy()
        self._flair_cache.clear()
