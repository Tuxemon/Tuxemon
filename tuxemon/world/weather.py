# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from tuxemon.database.runtime import db
from tuxemon.database.yaml_utils import load_yaml
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
        data = load_yaml(filepath)
        return WeatherTransitionRulesModel(**data)
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
    min_duration_seconds: int | None = Field(
        None,
        ge=0,
        description="Minimum duration in seconds before this transition is allowed. If None, transition is instantly eligible.",
    )
    max_duration_seconds: int | None = Field(
        None,
        ge=0,
        description="Maximum duration in seconds after which this transition is no longer allowed.",
    )
    required_temperature: Temperature | None = Field(
        None,
        description="The *current* temperature must match this to be eligible.",
    )
    required_wind: Wind | None = Field(
        None, description="The *current* wind must match this to be eligible."
    )
    temperature: Temperature | None = Field(
        None,
        description="General temperature category for the *next* weather.",
    )
    wind: Wind | None = Field(
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
        rules_model: WeatherTransitionRulesModel | None = None,
        seed: int | None = None,
    ) -> None:
        self._current_weather: Weather | None = None
        self._elapsed_duration_seconds: float = 0.0
        self._transition_rules_model: WeatherTransitionRulesModel | None = None
        self._last_transition_rule: WeatherTransitionRule | None = None
        self.transition_history: list[WeatherTransitionRecord] = []
        self._rng = (
            random.Random(seed) if seed is not None else random.Random()
        )
        logger.info(f"WorldWeatherManager initialized with seed: {seed}")

        if rules_model:
            self.load_rules_model(rules_model)

        self.set_weather(initial_slug)

    @property
    def current_weather(self) -> Weather | None:
        return self._current_weather

    @property
    def current_slug(self) -> str | None:
        return self._current_weather.slug if self._current_weather else None

    @property
    def last_transition(self) -> WeatherTransitionRule | None:
        return self._last_transition_rule

    @property
    def elapsed_time(self) -> float:
        return self._elapsed_duration_seconds

    def load_rules_model(self, model: WeatherTransitionRulesModel) -> None:
        self._transition_rules_model = model
        self.validate_rules()
        logger.info(
            f"Loaded transition rules model with {len(model.transitions)} weather states."
        )

    def validate_rules(self) -> None:
        if not self._transition_rules_model:
            return

        for slug, rules in self._transition_rules_model.transitions.items():
            for r in rules:
                if r.next_slug not in db.database["weather"]:
                    logger.warning(
                        f"Transition rule points to unknown weather slug '{r.next_slug}'"
                    )

    def set_weather(
        self, slug: str, rule: WeatherTransitionRule | None = None
    ) -> bool:
        """Sets the current weather state."""
        try:
            new_weather = Weather.get(slug)
        except Exception:
            logger.warning(f"Weather slug '{slug}' not found or invalid.")
            return False

        self._current_weather = new_weather
        self._elapsed_duration_seconds = 0.0
        self._last_transition_rule = rule
        logger.info(f"Weather set to: {self._current_weather.slug}")
        return True

    def advance_time(self, seconds: float) -> None:
        """Advances simulation time and processes transitions."""
        if seconds < 0:
            raise ValueError("Time cannot go backwards.")
        self._elapsed_duration_seconds += seconds
        self.advance_turn()

    def get_eligible_transitions(self) -> list[WeatherTransitionRule]:
        """Returns all transition rules currently eligible to trigger."""
        if not self._current_weather or not self._transition_rules_model:
            return []

        slug = self._current_weather.slug
        elapsed = self._elapsed_duration_seconds

        rules = self._transition_rules_model.transitions.get(slug, [])
        temp = self._current_weather.current_temperature
        wind = self._current_weather.current_wind

        eligible: list[WeatherTransitionRule] = []
        for r in rules:
            if (
                r.min_duration_seconds is not None
                and elapsed < r.min_duration_seconds
            ):
                continue
            if (
                r.max_duration_seconds is not None
                and elapsed > r.max_duration_seconds
            ):
                continue
            if (
                r.required_temperature is not None
                and r.required_temperature != temp
            ):
                continue
            if r.required_wind is not None and r.required_wind != wind:
                continue
            eligible.append(r)

        return eligible

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

        eligible = self.get_eligible_transitions()
        if not eligible:
            return

        total = sum(r.trigger_chance for r in eligible)
        roll = self._rng.random()

        if roll < total:
            weights = [r.trigger_chance for r in eligible]
            chosen = self._rng.choices(eligible, weights=weights, k=1)[0]
            current_slug = self._current_weather.slug
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
