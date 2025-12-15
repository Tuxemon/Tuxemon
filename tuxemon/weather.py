# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.db import Modifier, Temperature, WeatherModel, Wind, db

logger = logging.getLogger(__name__)


class Weather:
    """A weather class (sunny, freezing, etc.)."""

    _weathers: dict[str, Weather] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug = slug
        self.modifiers: list[Modifier] = []
        self._temperature: Optional[Temperature] = None
        self._wind: Optional[Wind] = None

        if self.slug:
            self.load(self.slug)

    def load(self, slug: str) -> None:
        """Loads weather."""

        if slug in Weather._weathers:
            cached_weather = Weather._weathers[slug]
            self.slug = slug
            self.modifiers = cached_weather.modifiers
            return

        results = WeatherModel.lookup(slug, db)
        self.modifiers = results.modifiers
        self._temperature = results.temperature
        self._wind = results.wind
        Weather._weathers[slug] = self

    @classmethod
    def get_weather(cls, slug: str) -> Optional[Weather]:
        """
        Retrieves a Weather object by its slug.

        Parameters:
            slug: The unique identifier for the weather.

        Returns:
            The Weather object if found, otherwise None.
        """
        return cls._weathers.get(slug)

    @classmethod
    def load_all_weathers(cls) -> None:
        """Loads all weathers from the database into the cache."""
        try:
            all_weather_slugs = list(db.database["weather"])
            for slug in all_weather_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all weathers: {e}")

    @classmethod
    def get_all_weathers(cls) -> dict[str, Weather]:
        """
        Returns all loaded weathers.

        Returns:
            A dictionary of all loaded Weather objects.
        """
        if not cls._weathers:
            cls.load_all_weathers()
        return cls._weathers

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the weather cache."""
        cls._weathers.clear()

    def __repr__(self) -> str:
        return f"Weather(slug={self.slug}, modifiers={self.modifiers})"

    @property
    def current_temperature(self) -> Temperature:
        """Returns the Temperature category loaded from the database model."""
        if self._temperature is None:
            raise RuntimeError(
                f"Temperature not loaded for weather slug: {self.slug}"
            )
        return self._temperature

    @property
    def current_wind(self) -> Wind:
        """Returns the Wind category loaded from the database model."""
        if self._wind is None:
            raise RuntimeError(
                f"Wind not loaded for weather slug: {self.slug}"
            )
        return self._wind
