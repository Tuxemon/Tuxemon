# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import random
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def pulse_pattern(
    pulses: int = 3, duration: float = 0.2, pause: float = 0.1
) -> list[tuple[float, float]]:
    """
    Generate a simple pulse pattern: rumble for `duration`, pause for `pause`.
    """
    return [(duration, pause) for _ in range(pulses)]


def heartbeat_pattern() -> list[tuple[float, float]]:
    """Simulate a heartbeat: short pulse, pause, longer pulse, pause."""
    return [
        (0.15, 0.1),  # first beat
        (0.25, 0.4),  # second beat, longer pause
    ]


def random_pattern(pulses: int = 5) -> list[tuple[float, float]]:
    """Generate a random rumble pattern with variable durations and pauses."""
    return [
        (random.uniform(0.1, 0.5), random.uniform(0.05, 0.3))
        for _ in range(pulses)
    ]


def explosion_pattern() -> list[tuple[float, float]]:
    """Simulate an explosion: strong rumble, fade out."""
    return [
        (0.5, 0.0),  # big initial blast
        (0.3, 0.1),  # aftershock
        (0.2, 0.2),  # fading rumble
    ]


def combine_patterns(
    *patterns: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Concatenate multiple patterns into one sequence."""
    sequence: list[tuple[float, float]] = []
    for p in patterns:
        sequence.extend(p)
    return sequence


def scale_pattern(
    pattern: list[tuple[float, float]], factor: float
) -> list[tuple[float, float]]:
    """Scale durations and pauses by a factor (speed up or slow down)."""
    return [(d * factor, p * factor) for d, p in pattern]


PatternFunc = Callable[..., list[tuple[float, float]]]

PATTERNS: dict[str, PatternFunc] = {
    "pulse": pulse_pattern,
    "heartbeat": heartbeat_pattern,
    "explosion": explosion_pattern,
    "random": random_pattern,
}


def register_pattern(name: str, func: PatternFunc) -> None:
    """Register a new rumble pattern function under the given name."""
    PATTERNS[name.lower()] = func


def get_pattern(name: str, **kwargs: Any) -> list[tuple[float, float]]:
    key = name.lower()
    if key not in PATTERNS:
        logger.error(
            f"Unknown rumble pattern: {name}. Available: {list(PATTERNS.keys())}"
        )
        raise ValueError(f"Unknown rumble pattern: {name}")
    return PATTERNS[key](**kwargs)
