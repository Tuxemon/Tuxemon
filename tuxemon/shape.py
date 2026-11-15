# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Any

from tuxemon.database.runtime import db
from tuxemon.db import AttributesModel, ShapeModel

logger = logging.getLogger(__name__)


class Shape:
    """A shape holds all the base values (speed, ranged, etc.)."""

    _shapes: dict[str, Shape] = {}

    def __init__(self, slug: str, attributes: AttributesModel) -> None:
        self.slug = slug
        self.attributes = attributes

    @classmethod
    def get(cls, slug: str) -> Shape:
        """
        Retrieve a Shape from cache or load it from the database.
        """
        if slug in cls._shapes:
            return cls._shapes[slug]

        try:
            results = ShapeModel.lookup(slug, db)
            attributes = results.attributes
        except Exception:
            logger.warning(f"Shape {slug} not found, using default.")
            attributes = AttributesModel(
                armour=1, dodge=1, hp=1, melee=1, ranged=1, speed=1
            )

        shape = cls(slug, attributes)
        cls._shapes[slug] = shape
        return shape

    @classmethod
    def load_all_shapes(cls) -> None:
        """Loads all shapes from the database into the cache."""
        try:
            for slug in db.database["shape"]:
                cls.get(slug)
        except Exception as e:
            logger.error(f"Failed to load all shapes: {e}")

    @classmethod
    def get_all_shapes(cls) -> dict[str, Shape]:
        """Returns all loaded shapes."""
        if not cls._shapes:
            cls.load_all_shapes()
        return cls._shapes

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the shape cache."""
        cls._shapes.clear()

    def __repr__(self) -> str:
        return f"Shape(slug={self.slug}, attributes={self.attributes})"


class ShapeHandler:
    """
    Provides gameplay logic derived from a Shape template.
    Each handler owns its own working copy of attributes,
    so mutations never affect the global Shape cache.
    """

    def __init__(self, shape_slug: str | None = None):
        slug = shape_slug or "default"
        template = Shape.get(slug)

        self._slug = slug
        self._attributes = AttributesModel(
            armour=template.attributes.armour,
            dodge=template.attributes.dodge,
            hp=template.attributes.hp,
            melee=template.attributes.melee,
            ranged=template.attributes.ranged,
            speed=template.attributes.speed,
        )

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def attributes(self) -> AttributesModel:
        return self._attributes

    def movement_cost(self, base_cost: int) -> float:
        """Lower cost if speed is high."""
        return base_cost / max(1, self._attributes.speed)

    def melee_damage(self, weapon_damage: int) -> int:
        """Shape influences melee output."""
        return weapon_damage + self._attributes.melee

    def ranged_damage(self, weapon_damage: int) -> int:
        """Shape influences ranged output."""
        return weapon_damage + self._attributes.ranged

    def dodge_chance(self, base_chance: float) -> float:
        """Shape modifies dodge probability."""
        return base_chance + (self._attributes.dodge * 0.02)

    def armour_reduction(self, incoming_damage: int) -> int:
        """Shape armour reduces incoming damage."""
        reduction = self._attributes.armour
        return max(0, incoming_damage - reduction)

    def apply_modifier(self, **kwargs: dict[str, Any]) -> None:
        """
        Apply temporary or permanent modifiers to this instance only.
        Example: handler.apply_modifier(speed=+1, melee=-2)
        """
        for key, delta in kwargs.items():
            if hasattr(self._attributes, key):
                current = getattr(self._attributes, key)
                setattr(self._attributes, key, current + delta)
