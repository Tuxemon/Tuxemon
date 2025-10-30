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
    including probability and duration constraints.
    """

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
    ) -> None:
        self._current_weather: Optional[Weather] = None
        self.start_timestamp: float = time.time()
        self._transition_rules_model: Optional[WeatherTransitionRulesModel] = (
            None
        )
        self._last_transition_rule: Optional[WeatherTransitionRule] = None
        self.transition_history: list[tuple[str, str, float]] = []

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
        return time.time() - self.start_timestamp

    def load_rules_model(self, model: WeatherTransitionRulesModel) -> None:
        self._transition_rules_model = model
        logger.info(
            f"Loaded transition rules model with {len(model.transitions)} weather states."
        )

    def set_weather(
        self, slug: str, rule: Optional[WeatherTransitionRule] = None
    ) -> bool:
        new_weather = Weather(slug)
        if new_weather.slug:
            self._current_weather = new_weather
            self.start_timestamp = time.time()
            self._last_transition_rule = rule
            logger.info(f"Weather set to: {self._current_weather.slug}")
            return True
        else:
            logger.warning(f"Weather slug '{slug}' not found.")
            return False

    def advance_turn(self) -> None:
        if not self._current_weather or not self._transition_rules_model:
            return

        current_slug = self._current_weather.slug
        elapsed = time.time() - self.start_timestamp

        if current_slug in self._transition_rules_model.transitions:
            eligible = [
                r
                for r in self._transition_rules_model.transitions[current_slug]
                if r.min_duration_seconds is not None
                and elapsed >= r.min_duration_seconds
                and (
                    r.max_duration_seconds is None
                    or elapsed <= r.max_duration_seconds
                )
            ]

            if eligible:
                total_transition_chance = sum(
                    r.trigger_chance for r in eligible
                )
                no_change_chance = max(0.0, 1.0 - total_transition_chance)

                # Create a temporary rule for "no change" to be included in random selection
                no_change_rule = WeatherTransitionRule(
                    next_slug=current_slug,
                    trigger_chance=no_change_chance,
                    min_duration_seconds=0,
                    max_duration_seconds=0,
                    temperature=None,
                    wind=None,
                )

                outcomes = eligible + [no_change_rule]
                weights = [r.trigger_chance for r in outcomes]

                chosen = random.choices(outcomes, weights=weights, k=1)[0]

                if chosen.next_slug != current_slug:
                    logger.info(
                        f"Transition triggered from '{current_slug}' to '{chosen.next_slug}'"
                    )
                    self.set_weather(chosen.next_slug, rule=chosen)
                    self.transition_history.append(
                        (current_slug, chosen.next_slug, time.time())
                    )
                else:
                    logger.debug(
                        f"Weather remains '{current_slug}' (No transition triggered)."
                    )

    def get_transition_history(self) -> list[tuple[str, str, float]]:
        return self.transition_history
