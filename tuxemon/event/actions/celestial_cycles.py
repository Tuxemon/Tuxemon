# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, final

import yaml

from tuxemon.constants import paths
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)

MAX_LENGTH: int = 365


@dataclass
class CelestialCycle:
    name: str
    phase_data: list[tuple[int, str]]


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open() as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


class Loader:
    _config_celestial_cycle: list[CelestialCycle] = []

    @classmethod
    def get_config_celestial_cycle(cls, filename: str) -> list[CelestialCycle]:
        yaml_path = paths.mods_folder / filename
        if not cls._config_celestial_cycle:
            raw_data = load_yaml(yaml_path)
            cls._config_celestial_cycle = [
                CelestialCycle(
                    name=item["name"], phase_data=item["phase_data"]
                )
                for item in raw_data
            ]
        return cls._config_celestial_cycle


@final
@dataclass
class CelestialCyclesAction(EventAction):
    """
    Loads the celestial cycles into game variables.
    """

    name = "celestial_cycles"

    def start(self, session: Session) -> None:
        player = session.player
        day_of_year = int(player.game_variables.get("day_of_year", 1))
        bodies = Loader.get_config_celestial_cycle(f"{self.name}.yaml")

        for body in bodies:
            validate_celestial_data(body)
            phase = get_celestial_phase(day_of_year, body.phase_data)
            player.game_variables[body.name] = phase


def validate_celestial_data(celestial_cycle: CelestialCycle) -> None:
    """Validates a celestial cycle for phase lengths and translations."""
    validate_phase_lengths(celestial_cycle.phase_data)
    validate_translations(celestial_cycle.phase_data)


def validate_translations(phase_data: list[tuple[int, str]]) -> None:
    """Validates that all phase names have translations in en_US."""
    for _, name in phase_data:
        if not T.has_translation("en_US", name):
            logger.error(f"Missing translation for phase: {name}")


def validate_phase_lengths(phase_data: list[tuple[int, str]]) -> None:
    """Validates that the total phase lengths match MAX_LENGTH."""
    total_length = sum(length for length, _ in phase_data)
    if total_length != MAX_LENGTH:
        raise ValueError(
            f"Invalid phase lengths: Total lengths {total_length} do not equal {MAX_LENGTH}."
        )


def get_celestial_phase(
    target_day_of_year: int,
    phase_data: list[tuple[int, str]],
) -> str:
    """Gets the fictional celestial phase for a specific day of year."""

    phase_length = sum(length for length, _ in phase_data)
    if phase_length != MAX_LENGTH:
        raise ValueError(
            f"Total phase lengths {phase_length} must be equal to {MAX_LENGTH} days."
        )

    normalized_day = target_day_of_year % 365

    current_day = 0
    for length, name in phase_data:
        current_day += length
        if normalized_day < current_day:
            return name

    return phase_data[-1][1]
