# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.db import db

logger = logging.getLogger(__name__)


class Terrain:
    """A terrain class (mountain, underground, etc)."""

    _terrains: dict[str, Terrain] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug = slug
        self.element_modifier: dict[str, float] = {}

        if self.slug:
            self.load(self.slug)

    def load(self, slug: str) -> None:
        """Loads terrain."""

        if slug in Terrain._terrains:
            cached_terrain = Terrain._terrains[slug]
            self.slug = slug
            self.element_modifier = cached_terrain.element_modifier
            return

        try:
            results = db.lookup(slug, table="terrain")
        except KeyError:
            raise RuntimeError(f"Terrain {slug} not found")

        self.element_modifier = results.element_modifier

        Terrain._terrains[slug] = self

    @classmethod
    def get_terrain(cls, slug: str) -> Optional[Terrain]:
        """
        Retrieves a Terrain object by its slug.

        Parameters:
            slug: The unique identifier for the terrain.

        Returns:
            The Terrain object if found, otherwise None.
        """
        return cls._terrains.get(slug)

    @classmethod
    def load_all_terrains(cls) -> None:
        """Loads all terrains from the database into the cache."""
        try:
            all_terrain_slugs = list(db.database["terrain"])
            for slug in all_terrain_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all terrains: {e}")

    @classmethod
    def get_all_terrains(cls) -> dict[str, Terrain]:
        """
        Returns all loaded terrains.

        Returns:
            A dictionary of all loaded Terrain objects.
        """
        if not cls._terrains:
            cls.load_all_terrains()
        return cls._terrains

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the terrain cache."""
        cls._terrains.clear()

    def __repr__(self) -> str:
        return f"Terrain(slug={self.slug}, element_modifier={self.element_modifier})"
