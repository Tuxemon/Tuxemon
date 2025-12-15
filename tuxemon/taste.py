# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from typing import Optional

from tuxemon.db import TasteModel, db
from tuxemon.locale import T
from tuxemon.modifiers import ModifiersHandler

logger = logging.getLogger(__name__)


class Taste:
    """A taste can be warm or cold and it modifiers the monster's stats."""

    _tastes: dict[str, Taste] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug: str = ""
        self.taste_type: str = ""
        self.rarity_score: float = 1.0
        self.modifiers: ModifiersHandler = ModifiersHandler()

        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads a taste."""

        if slug in Taste._tastes:
            cached_taste = Taste._tastes[slug]
            self.slug = slug
            self.modifiers = cached_taste.modifiers
            self.taste_type = cached_taste.taste_type
            self.rarity_score = cached_taste.rarity_score
            return

        results = TasteModel.lookup(slug, db)
        self.slug = slug
        self.modifiers = ModifiersHandler(list(results.modifiers))
        self.taste_type = results.taste_type
        self.rarity_score = results.rarity_score

        Taste._tastes[slug] = self

    @property
    def name(self) -> str:
        """Translated display name for this taste."""
        return T.translate(self.slug) if self.slug else ""

    @property
    def description(self) -> str:
        """Translated description for this taste."""
        return T.translate(f"{self.slug}_description") if self.slug else ""

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

    @classmethod
    def weighted_choice(cls, tastes: list[Taste]) -> str:
        """Selects a taste slug based on rarity weights."""
        if not tastes:
            return "tasteless"
        weights = [taste.rarity_score for taste in tastes]
        return random.choices(tastes, weights=weights, k=1)[0].slug

    @classmethod
    def get_random_taste_excluding(
        cls,
        taste_type: str,
        exclude_slugs: Sequence[str],
        use_rarity: bool = True,
    ) -> Optional[str]:
        """
        Returns a random taste slug of a given type, excluding specified slugs.
        Optionally weights the selection based on rarity_score.

        Notes:
            - If use_rarity=True, selection is weighted by rarity_score (0.0 to 1.0).
            - Tastes with rarity_score=0.0 will never be selected.
            - If no eligible tastes are found (or all rarity_scores are 0.0),
                the method returns None.
        """
        eligible_tastes = [
            taste
            for taste in cls.get_all_tastes().values()
            if taste.taste_type == taste_type
            and taste.slug not in exclude_slugs
        ]

        if not eligible_tastes:
            return None

        if use_rarity:
            weights = [taste.rarity_score for taste in eligible_tastes]
            return random.choices(eligible_tastes, weights=weights, k=1)[
                0
            ].slug
        else:
            return random.choice(eligible_tastes).slug

    @classmethod
    def generate(
        cls, cold_slug: str = "tasteless", warm_slug: str = "tasteless"
    ) -> tuple[str, str]:
        """
        Generates initial cold and warm tastes.
        If 'tasteless', a random taste of that type is chosen.
        """
        if cold_slug == "tasteless":
            cold_slug = (
                cls.get_random_taste_excluding(
                    "cold", exclude_slugs=["tasteless"], use_rarity=True
                )
                or "tasteless"
            )

        if warm_slug == "tasteless":
            warm_slug = (
                cls.get_random_taste_excluding(
                    "warm", exclude_slugs=["tasteless"], use_rarity=True
                )
                or "tasteless"
            )

        return cold_slug, warm_slug

    def __repr__(self) -> str:
        return (
            f"Taste(slug={self.slug}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"modifier={self.modifiers}, "
            f"type={self.taste_type})"
        )
