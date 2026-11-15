# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml

if TYPE_CHECKING:
    from tuxemon.session import AbstractSession

logger = logging.getLogger(__name__)


@dataclass
class CelestialCycle:
    name: str
    length: int
    phase_data: list[tuple[int, str]]


class Loader:
    _config_celestial_cycle: list[CelestialCycle] = []

    @classmethod
    def get_config_celestial_cycle(cls, filename: str) -> list[CelestialCycle]:
        yaml_path = paths.mods_folder / filename
        if not cls._config_celestial_cycle:
            raw_data = load_yaml(yaml_path)
            cls._config_celestial_cycle = [
                CelestialCycle(
                    name=item["name"],
                    length=item["length"],
                    phase_data=item["phase_data"],
                )
                for item in raw_data
            ]
        return cls._config_celestial_cycle


@dataclass
class CelestialHandler:
    """
    Provides access to fictional celestial phases (e.g., moon, sun) based on
    the real-world day_of_year from the session's TimeHandler.

    Phases are computed on demand from the configured celestial_cycles.yaml
    data and are not stored in game_variables.
    """

    session: AbstractSession[Any]
    _cycles: list[CelestialCycle]
    _cache_day: int | None = None
    _cache_phases: dict[str, str] | None = None

    @classmethod
    def from_session(cls, session: AbstractSession[Any]) -> CelestialHandler:
        bodies = Loader.get_config_celestial_cycle("celestial_cycles.yaml")

        for body in bodies:
            validate_celestial_data(body)

        return cls(session=session, _cycles=bodies)

    def _find_cycle(self, name: str) -> CelestialCycle:
        for cycle in self._cycles:
            if cycle.name == name:
                return cycle
        raise KeyError(
            f"Unknown celestial body '{name}'. "
            f"Available bodies: {', '.join(self.list_bodies())}"
        )

    def get_phase(self, name: str) -> str:
        day_of_year = self.session.time.get_time_variables().day_of_year
        cycle = self._find_cycle(name)
        return get_celestial_phase(day_of_year, cycle)

    def get_all_phases(self) -> dict[str, str]:
        day_of_year = self.session.time.get_time_variables().day_of_year

        if self._cache_day == day_of_year and self._cache_phases is not None:
            return self._cache_phases

        phases = {
            body.name: get_celestial_phase(day_of_year, body)
            for body in self._cycles
        }

        self._cache_day = day_of_year
        self._cache_phases = phases
        return phases

    def iter_phases(self) -> Iterable[tuple[str, str]]:
        day_of_year = self.session.time.get_time_variables().day_of_year
        for body in self._cycles:
            yield body.name, get_celestial_phase(day_of_year, body)

    def list_bodies(self) -> list[str]:
        return [cycle.name for cycle in self._cycles]

    def list_phases(self, name: str) -> list[str]:
        cycle = self._find_cycle(name)
        return [phase_name for _, phase_name in cycle.phase_data]


def validate_celestial_data(cycle: CelestialCycle) -> None:
    validate_phase_lengths(cycle.name, cycle.length, cycle.phase_data)


def validate_phase_lengths(
    name: str, length: int, phase_data: list[tuple[int, str]]
) -> None:
    if length <= 0:
        raise ValueError(
            f"Celestial cycle '{name}' must have a positive length, got {length}."
        )

    total_length = sum(l for l, _ in phase_data)
    if total_length != length:
        raise ValueError(
            f"Celestial cycle '{name}' has invalid total length {total_length}; "
            f"expected {length}."
        )


def get_celestial_phase(target_day_of_year: int, cycle: CelestialCycle) -> str:
    if not cycle.phase_data:
        raise ValueError(f"Celestial cycle '{cycle.name}' has no phase data.")

    total_length = sum(l for l, _ in cycle.phase_data)
    if total_length != cycle.length:
        raise ValueError(
            f"Celestial cycle '{cycle.name}' has invalid total length {total_length}; "
            f"expected {cycle.length}."
        )

    normalized_day = target_day_of_year % cycle.length

    current_day = 0
    for length, name in cycle.phase_data:
        current_day += length
        if normalized_day < current_day:
            return name

    return cycle.phase_data[-1][1]


def get_phase_progress(
    target_day_of_year: int, cycle: CelestialCycle
) -> tuple[str, int, int]:
    """
    Returns (phase_name, day_in_phase, phase_length).
    """

    if not cycle.phase_data:
        raise ValueError(f"Celestial cycle '{cycle.name}' has no phase data.")

    normalized_day = target_day_of_year % cycle.length

    current_day = 0
    for length, name in cycle.phase_data:
        next_day = current_day + length
        if normalized_day < next_day:
            day_in_phase = normalized_day - current_day
            return name, day_in_phase, length
        current_day = next_day

    # fallback (should never happen if validated)
    last_length, last_name = cycle.phase_data[-1]
    return last_name, last_length - 1, last_length
