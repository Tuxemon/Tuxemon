# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.database.runtime import db
from tuxemon.db import Modifier, Temperature, WeatherModel, Wind

logger = logging.getLogger(__name__)


class Weather:
    """A weather class (sunny, freezing, etc.)."""

    _weathers: dict[str, Weather] = {}

    def __init__(
        self,
        slug: str,
        modifiers: list[Modifier],
        temperature: Temperature | None,
        wind: Wind | None,
    ) -> None:
        self.slug = slug
        self.modifiers = list(modifiers)
        self._temperature = temperature
        self._wind = wind

    @classmethod
    def get(cls, slug: str) -> Weather:
        """
        Retrieve a Weather from cache or load it from the database.
        """
        if slug in cls._weathers:
            return cls._weathers[slug]

        try:
            model = WeatherModel.lookup(slug, db)
            modifiers = model.modifiers
            temperature = model.temperature
            wind = model.wind
        except Exception:
            logger.warning(f"Weather {slug} not found, using empty fallback.")
            modifiers = []
            temperature = None
            wind = None

        weather = cls(slug, modifiers, temperature, wind)
        cls._weathers[slug] = weather
        return weather

    @classmethod
    def load_all_weathers(cls) -> None:
        """Loads all weathers from the database into the cache."""
        try:
            for slug in db.database["weather"]:
                cls.get(slug)
        except Exception as e:
            logger.error(f"Failed to load all weathers: {e}")

    @classmethod
    def get_all_weathers(cls) -> dict[str, Weather]:
        """Returns all loaded weathers."""
        if not cls._weathers:
            cls.load_all_weathers()
        return cls._weathers

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the weather cache."""
        cls._weathers.clear()

    @property
    def current_temperature(self) -> Temperature:
        if self._temperature is None:
            raise RuntimeError(
                f"Temperature not loaded for weather slug: {self.slug}"
            )
        return self._temperature

    @property
    def current_wind(self) -> Wind:
        if self._wind is None:
            raise RuntimeError(
                f"Wind not loaded for weather slug: {self.slug}"
            )
        return self._wind

    def __repr__(self) -> str:
        return (
            f"Weather(slug={self.slug}, "
            f"modifiers={self.modifiers}, "
            f"temperature={self._temperature}, "
            f"wind={self._wind})"
        )
