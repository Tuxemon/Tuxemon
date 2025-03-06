# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.db import db

logger = logging.getLogger(__name__)


class Shape:
    """A shape holds all the values (speed, ranged, etc.)."""

    _shapes: dict[str, Shape] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug = slug
        self.armour: int = 1
        self.dodge: int = 1
        self.hp: int = 1
        self.melee: int = 1
        self.ranged: int = 1
        self.speed: int = 1

        if self.slug:
            self.load(self.slug)

    def load(self, slug: str) -> None:
        """Loads shape."""

        if slug in Shape._shapes:
            cached_shape = Shape._shapes[slug]
            self.slug = slug
            self.armour = cached_shape.armour
            self.dodge = cached_shape.dodge
            self.hp = cached_shape.hp
            self.melee = cached_shape.melee
            self.ranged = cached_shape.ranged
            self.speed = cached_shape.speed
            return

        try:
            results = db.lookup(slug, table="shape")
        except KeyError:
            raise RuntimeError(f"Shape {slug} not found")

        self.armour = results.armour
        self.dodge = results.dodge
        self.hp = results.hp
        self.melee = results.melee
        self.ranged = results.ranged
        self.speed = results.speed

        Shape._shapes[slug] = self

    @classmethod
    def get_shape(cls, slug: str) -> Optional[Shape]:
        """
        Retrieves a Shape object by its slug.

        Parameters:
            slug: The unique identifier for the shape.

        Returns:
            The Shape object if found, otherwise None.
        """
        return cls._shapes.get(slug)

    @classmethod
    def load_all_shapes(cls) -> None:
        """Loads all shapes from the database into the cache."""
        try:
            all_shape_slugs = list(db.database["shape"])
            for slug in all_shape_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all shapes: {e}")

    @classmethod
    def get_all_shapes(cls) -> dict[str, Shape]:
        """
        Returns all loaded shapes.

        Returns:
            A dictionary of all loaded Shape objects.
        """
        if not cls._shapes:
            cls.load_all_shapes()
        return cls._shapes

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the shape cache."""
        cls._shapes.clear()

    def __repr__(self) -> str:
        return (
            f"Shape(slug={self.slug}, armour={self.armour}, dodge={self.dodge}, "
            f"hp={self.hp}, melee={self.melee}, ranged={self.ranged}, speed={self.speed})"
        )
