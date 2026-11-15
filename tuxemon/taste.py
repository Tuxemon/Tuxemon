# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence

from tuxemon.database.runtime import db
from tuxemon.db import TasteModel
from tuxemon.locale.locale import T
from tuxemon.modifiers import ModifiersHandler

logger = logging.getLogger(__name__)


class Taste:
    """A taste can be warm or cold and it modifies the monster's stats."""

    _tastes: dict[str, Taste] = {}

    def __init__(
        self,
        slug: str,
        taste_type: str,
        rarity_score: float,
        modifiers: ModifiersHandler,
    ) -> None:
        self.slug = slug
        self.taste_type = taste_type
        self.rarity_score = rarity_score
        self.modifiers = modifiers

    @classmethod
    def get(cls, slug: str) -> Taste:
        """
        Retrieve a Taste from cache or load it from the database.
        """
        if slug in cls._tastes:
            return cls._tastes[slug]

        if slug == "tasteless":
            taste = cls(
                slug="tasteless",
                taste_type="neutral",
                rarity_score=1.0,
                modifiers=ModifiersHandler([]),
            )
            cls._tastes[slug] = taste
            return taste

        try:
            model = TasteModel.lookup(slug, db)
            taste = cls(
                slug=slug,
                taste_type=model.taste_type,
                rarity_score=model.rarity_score,
                modifiers=ModifiersHandler(list(model.modifiers)),
            )
        except Exception:
            logger.warning(f"Taste {slug} not found, using fallback.")
            taste = cls(
                slug=slug,
                taste_type="",
                rarity_score=1.0,
                modifiers=ModifiersHandler(),
            )

        cls._tastes[slug] = taste
        return taste

    @classmethod
    def load_all_tastes(cls) -> None:
        """Loads all tastes from the database into the cache."""
        try:
            for slug in db.database["taste"]:
                cls.get(slug)
        except Exception as e:
            logger.error(f"Failed to load all tastes: {e}")

    @classmethod
    def get_all_tastes(cls) -> dict[str, Taste]:
        """Returns all loaded tastes."""
        if not cls._tastes:
            cls.load_all_tastes()
        return cls._tastes

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the taste cache."""
        cls._tastes.clear()

    @property
    def name(self) -> str:
        return T.translate(self.slug) if self.slug else ""

    @property
    def description(self) -> str:
        return T.translate(f"{self.slug}_description") if self.slug else ""

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
    ) -> str | None:
        eligible = [
            t
            for t in cls.get_all_tastes().values()
            if t.taste_type == taste_type and t.slug not in exclude_slugs
        ]

        if not eligible:
            return None

        if use_rarity:
            weights = [t.rarity_score for t in eligible]
            return random.choices(eligible, weights=weights, k=1)[0].slug

        return random.choice(eligible).slug

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

    def get_multiplier(self, stat_name: str) -> float:
        """
        Returns the combined multiplier for a given stat based on this taste's modifiers.
        """
        multiplier = 1.0
        for modifier in self.modifiers:
            if stat_name in modifier.values:
                multiplier *= modifier.multiplier
        return multiplier

    def apply_to_stat(self, stat_name: str, value: int) -> int:
        """
        Applies this taste's modifiers to a stat value and returns the modified result.
        """
        return round(value * self.get_multiplier(stat_name))

    def __repr__(self) -> str:
        return (
            f"Taste(slug={self.slug}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"type={self.taste_type}, "
            f"rarity={self.rarity_score}, "
            f"modifiers={self.modifiers})"
        )
