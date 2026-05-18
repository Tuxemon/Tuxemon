# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.database.runtime import db
from tuxemon.db import Modifier, TerrainModel

logger = logging.getLogger(__name__)


class Terrain:
    """A terrain class (mountain, underground, etc)."""

    _terrains: dict[str, Terrain] = {}

    def __init__(self, slug: str, modifiers: list[Modifier]) -> None:
        self.slug = slug
        self.modifiers = list(modifiers)

    @classmethod
    def get(cls, slug: str) -> Terrain:
        """
        Retrieve a Terrain from cache or load it from the database.
        """
        if slug in cls._terrains:
            return cls._terrains[slug]

        try:
            model = TerrainModel.lookup(slug, db)
            modifiers = model.modifiers
        except Exception:
            logger.warning(f"Terrain {slug} not found, using empty fallback.")
            modifiers = []

        terrain = cls(slug, modifiers)
        cls._terrains[slug] = terrain
        return terrain

    @classmethod
    def load_all_terrains(cls) -> None:
        """Loads all terrains from the database into the cache."""
        try:
            for slug in db.database["terrain"]:
                cls.get(slug)
        except Exception as e:
            logger.error(f"Failed to load all terrains: {e}")

    @classmethod
    def get_all_terrains(cls) -> dict[str, Terrain]:
        """Returns all loaded terrains."""
        if not cls._terrains:
            cls.load_all_terrains()
        return cls._terrains

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the terrain cache."""
        cls._terrains.clear()

    def __repr__(self) -> str:
        return f"Terrain(slug={self.slug}, modifiers={self.modifiers})"
