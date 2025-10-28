# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import time
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from tuxemon.weather import Weather

logger = logging.getLogger(__name__)


class Temperature(str, Enum):
    freezing = "freezing"
    cold = "cold"
    mild = "mild"
    warm = "warm"
    hot = "hot"
    scorching = "scorching"


class Wind(str, Enum):
    calm = "calm"
    breezy = "breezy"
    windy = "windy"
    gusty = "gusty"
    stormy = "stormy"


def load_weather_previsions(filepath: Path) -> WeatherPrevisionModel:
    try:
        with filepath.open() as file:
            data = yaml.safe_load(file)
            return WeatherPrevisionModel(**data)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Error loading WeatherPrevisionModel: {exc}")
        raise


class WeatherPrevision(BaseModel):
    next_slug: str = Field(
        ..., description="The weather slug to transition to."
    )
    trigger_chance: float = Field(..., ge=0.0, le=1.0)
    min_duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum duration in seconds before this transition is allowed. If None, transition is disabled.",
    )
    max_duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum duration in seconds after which this transition is no longer allowed.",
    )
    temperature: Optional[Temperature] = Field(
        None, description="General temperature category for this transition."
    )
    wind: Optional[Wind] = Field(
        None, description="Wind intensity level for this transition."
    )


class WeatherPrevisionModel(BaseModel):
    previsions: dict[str, list[WeatherPrevision]]

    @model_validator(mode="after")
    def check_cumulative_chance(self) -> Any:
        """
        Custom validator to ensure the total transition chance for any given
        starting weather does not exceed 1.0 (100%).
        """
        for current_slug, transitions in self.previsions.items():
            total_chance = sum(p.trigger_chance for p in transitions)
            if total_chance > 1.0 + 1e-6:
                raise ValueError(
                    f"Cumulative trigger chance for weather '{current_slug}' "
                    f"is {total_chance:.3f}, which exceeds 1.0."
                )
        return self

    @model_validator(mode="after")
    def check_duration_bounds(self) -> Any:
        for transitions in self.previsions.values():
            for p in transitions:
                if (
                    p.min_duration_seconds is not None
                    and p.max_duration_seconds is not None
                ):
                    if p.max_duration_seconds < p.min_duration_seconds:
                        raise ValueError(
                            f"max_duration_seconds ({p.max_duration_seconds}) is less than min_duration_seconds ({p.min_duration_seconds}) for transition to '{p.next_slug}'"
                        )
        return self


class WorldWeatherManager:
    """
    Manages the global weather state, holding the validated Pydantic prevision model.
    """

    def __init__(
        self,
        initial_slug: str = "sunny",
        previsions_model: Optional[WeatherPrevisionModel] = None,
    ) -> None:
        self._current_weather: Optional[Weather] = None
        self.start_timestamp: float = time.time()
        self._previsions_model: Optional[WeatherPrevisionModel] = None
        self._last_transition: Optional[WeatherPrevision] = None
        self.transition_history: list[tuple[str, str, float]] = []

        if previsions_model:
            self.load_previsions_model(previsions_model)

        self.set_weather(initial_slug)

    @property
    def current_weather(self) -> Optional[Weather]:
        return self._current_weather

    @property
    def current_slug(self) -> Optional[str]:
        return self._current_weather.slug if self._current_weather else None

    @property
    def last_transition(self) -> Optional[WeatherPrevision]:
        return self._last_transition

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_timestamp

    def load_previsions_model(self, model: WeatherPrevisionModel) -> None:
        self._previsions_model = model
        logger.info(
            f"Loaded prevision model with {len(model.previsions)} weather states."
        )

    def set_weather(
        self, slug: str, transition: Optional[WeatherPrevision] = None
    ) -> bool:
        new_weather = Weather(slug)
        if new_weather.slug:
            self._current_weather = new_weather
            self.start_timestamp = time.time()
            self._last_transition = transition
            logger.info(f"Weather set to: {self._current_weather.slug}")
            return True
        else:
            logger.warning(f"Weather slug '{slug}' not found.")
            return False

    def advance_turn(self) -> None:
        if not self._current_weather or not self._previsions_model:
            return

        current_slug = self._current_weather.slug
        elapsed = time.time() - self.start_timestamp

        if current_slug in self._previsions_model.previsions:
            eligible = [
                p
                for p in self._previsions_model.previsions[current_slug]
                if p.min_duration_seconds is not None
                and elapsed >= p.min_duration_seconds
                and (
                    p.max_duration_seconds is None
                    or elapsed <= p.max_duration_seconds
                )
            ]

            if eligible:
                total_transition_chance = sum(
                    p.trigger_chance for p in eligible
                )
                no_change_chance = max(0.0, 1.0 - total_transition_chance)

                outcomes = eligible + [
                    WeatherPrevision(
                        next_slug=current_slug,
                        trigger_chance=no_change_chance,
                        min_duration_seconds=0,
                        max_duration_seconds=0,
                        temperature=None,
                        wind=None,
                    )
                ]
                weights = [p.trigger_chance for p in outcomes]

                chosen = random.choices(outcomes, weights=weights, k=1)[0]

                if chosen.next_slug != current_slug:
                    logger.info(
                        f"Transition triggered from '{current_slug}' to '{chosen.next_slug}'"
                    )
                    self.set_weather(chosen.next_slug, transition=chosen)
                    self.transition_history.append(
                        (current_slug, chosen.next_slug, time.time())
                    )
                else:
                    logger.debug(
                        f"Weather remains '{current_slug}' (No transition triggered)."
                    )

    def get_transition_history(self) -> list[tuple[str, str, float]]:
        return self.transition_history
