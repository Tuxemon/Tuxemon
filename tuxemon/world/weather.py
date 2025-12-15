# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from tuxemon.db import Temperature, Wind
from tuxemon.weather import Weather

logger = logging.getLogger(__name__)


@dataclass
class WeatherTransitionRecord:
    from_slug: str
    to_slug: str
    sim_time: float
    real_time: float = field(default_factory=time.time)


def load_weather_transition_rules(
    filepath: Path,
) -> WeatherTransitionRulesModel:
    """Loads and validates the weather transition rules from a YAML file."""
    try:
        with filepath.open() as file:
            data = yaml.safe_load(file)
            return WeatherTransitionRulesModel(**data)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Error loading WeatherTransitionRulesModel: {exc}")
        raise


class WeatherTransitionRule(BaseModel):
    """
    Defines a rule for transitioning from a current weather state to a next one,
    including probability, duration, and context constraints.
    """

    next_slug: str = Field(
        ..., description="The weather slug to transition to."
    )
    trigger_chance: float = Field(..., ge=0.0, le=1.0)
    min_duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum duration in seconds before this transition is allowed. If None, transition is instantly eligible.",
    )
    max_duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum duration in seconds after which this transition is no longer allowed.",
    )
    required_temperature: Optional[Temperature] = Field(
        None,
        description="The *current* temperature must match this to be eligible.",
    )
    required_wind: Optional[Wind] = Field(
        None, description="The *current* wind must match this to be eligible."
    )
    temperature: Optional[Temperature] = Field(
        None,
        description="General temperature category for the *next* weather.",
    )
    wind: Optional[Wind] = Field(
        None, description="Wind intensity level for the *next* weather."
    )


class WeatherTransitionRulesModel(BaseModel):
    """
    A model holding the complete set of weather transition rules, keyed by
    the current weather slug.
    """

    transitions: dict[str, list[WeatherTransitionRule]]

    @model_validator(mode="after")
    def check_cumulative_chance(self) -> Any:
        """
        Custom validator to ensure the total transition chance for any given
        starting weather does not exceed 1.0 (100%).
        """
        for current_slug, rules in self.transitions.items():
            total_chance = sum(p.trigger_chance for p in rules)
            if total_chance > 1.0 + 1e-6:
                raise ValueError(
                    f"Cumulative trigger chance for weather '{current_slug}' "
                    f"is {total_chance:.3f}, which exceeds 1.0."
                )
        return self

    @model_validator(mode="after")
    def check_duration_bounds(self) -> Any:
        for rules in self.transitions.values():
            for p in rules:
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
    Manages the global weather state, holding the validated Pydantic transition rules model.
    """

    def __init__(
        self,
        initial_slug: str = "sunny",
        rules_model: Optional[WeatherTransitionRulesModel] = None,
        seed: Optional[int] = None,
    ) -> None:
        self._current_weather: Optional[Weather] = None
        self._elapsed_duration_seconds: float = 0.0
        self._transition_rules_model: Optional[WeatherTransitionRulesModel] = (
            None
        )
        self._last_transition_rule: Optional[WeatherTransitionRule] = None
        self.transition_history: list[WeatherTransitionRecord] = []
        self._rng = (
            random.Random(seed) if seed is not None else random.Random()
        )
        logger.info(f"WorldWeatherManager initialized with seed: {seed}")

        if rules_model:
            self.load_rules_model(rules_model)

        self.set_weather(initial_slug)

    @property
    def current_weather(self) -> Optional[Weather]:
        return self._current_weather

    @property
    def current_slug(self) -> Optional[str]:
        return self._current_weather.slug if self._current_weather else None

    @property
    def last_transition(self) -> Optional[WeatherTransitionRule]:
        return self._last_transition_rule

    @property
    def elapsed_time(self) -> float:
        return self._elapsed_duration_seconds

    def load_rules_model(self, model: WeatherTransitionRulesModel) -> None:
        self._transition_rules_model = model
        logger.info(
            f"Loaded transition rules model with {len(model.transitions)} weather states."
        )

    def set_weather(
        self, slug: str, rule: Optional[WeatherTransitionRule] = None
    ) -> bool:
        """Sets the current weather state."""
        try:
            new_weather = Weather(slug)
        except Exception:
            logger.warning(f"Weather slug '{slug}' not found or invalid.")
            return False

        self._current_weather = new_weather
        self._elapsed_duration_seconds = 0.0
        self._last_transition_rule = rule
        logger.info(f"Weather set to: {self._current_weather.slug}")
        return True

    def force_transition(self, new_slug: str) -> None:
        """Forces an immediate weather transition and records it."""
        old_slug = self.current_slug or "UNKNOWN"
        elapsed_before = self._elapsed_duration_seconds

        if self.set_weather(new_slug, rule=None):
            self.transition_history.append(
                WeatherTransitionRecord(
                    from_slug=old_slug,
                    to_slug=new_slug,
                    sim_time=elapsed_before,
                )
            )
            logger.info(f"Weather forced from '{old_slug}' to '{new_slug}'")
        else:
            logger.warning(
                f"Could not force transition to unknown slug: {new_slug}"
            )

    def update(self, dt: float) -> None:
        self._elapsed_duration_seconds += dt
        self.advance_turn()

    def advance_turn(self) -> None:
        if not self._current_weather or not self._transition_rules_model:
            return

        current_slug = self._current_weather.slug
        elapsed = self._elapsed_duration_seconds

        if current_slug not in self._transition_rules_model.transitions:
            logger.warning(
                f"No transition rules found for current weather '{current_slug}'. Weather is stuck."
            )
            return

        rules = self._transition_rules_model.transitions[current_slug]

        current_temp = self._current_weather.current_temperature
        current_wind = self._current_weather.current_wind

        eligible: list[WeatherTransitionRule] = []
        for r in rules:
            is_time_eligible = (
                r.min_duration_seconds is None
                or elapsed >= r.min_duration_seconds
            ) and (
                r.max_duration_seconds is None
                or elapsed <= r.max_duration_seconds
            )

            is_temp_eligible = (
                r.required_temperature is None
                or r.required_temperature == current_temp
            )
            is_wind_eligible = (
                r.required_wind is None or r.required_wind == current_wind
            )

            if is_time_eligible and is_temp_eligible and is_wind_eligible:
                eligible.append(r)

        if eligible:
            total_transition_chance = sum(r.trigger_chance for r in eligible)

            if self._rng.random() < total_transition_chance:
                weights = [r.trigger_chance for r in eligible]
                chosen = self._rng.choices(eligible, weights=weights, k=1)[0]

                logger.info(
                    f"Transition triggered from '{current_slug}' to '{chosen.next_slug}'"
                )

                elapsed_before = self._elapsed_duration_seconds
                self.set_weather(chosen.next_slug, rule=chosen)

                self.transition_history.append(
                    WeatherTransitionRecord(
                        from_slug=current_slug,
                        to_slug=chosen.next_slug,
                        sim_time=elapsed_before,
                    )
                )

    def get_transition_history(self) -> list[WeatherTransitionRecord]:
        return self.transition_history
