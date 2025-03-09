# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from tuxemon.db import Modifier, db
from tuxemon.locale import T

logger = logging.getLogger(__name__)


class Taste:
    """A taste can be warm or cold and it modifiers the monster's stats."""

    _tastes: dict[str, Taste] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.name: str = ""
        self.taste_type: str = ""
        self.modifiers: Sequence[Modifier] = []

        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads a taste."""

        if slug in Taste._tastes:
            cached_taste = Taste._tastes[slug]
            self.slug = slug
            self.name = cached_taste.name
            self.modifiers = cached_taste.modifiers
            self.taste_type = cached_taste.taste_type
            return

        try:
            results = db.lookup(slug, table="taste")
        except KeyError:
            raise RuntimeError(f"Taste {slug} not found")

        self.slug = slug
        self.name = T.translate(self.slug)
        self.modifiers = results.modifiers
        self.taste_type = results.taste_type

        Taste._tastes[slug] = self

    @classmethod
    def get_taste(cls, slug: str) -> Optional[Taste]:
        """Retrieves a Taste object by its slug.

        Parameters:
            slug: The unique identifier for the taste.

        Returns:
            The Taste object if found, otherwise None.
        """
        return cls._tastes.get(slug)

    @classmethod
    def load_all_tastes(cls) -> None:
        """Loads all tastes from the database into the cache."""
        try:
            all_taste_slugs = list(db.database["taste"])
            for slug in all_taste_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all tastes: {e}")

    @classmethod
    def get_all_tastes(cls) -> dict[str, Taste]:
        """Returns all loaded tastes.

        Returns:
            A dictionary of all loaded Taste objects.
        """
        if not cls._tastes:
            cls.load_all_tastes()
        return cls._tastes

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the taste cache."""
        cls._tastes.clear()

    def __repr__(self) -> str:
        return f"Taste(slug={self.slug}, name={self.name}, modifier={self.modifiers}, type={self.taste_type})"
