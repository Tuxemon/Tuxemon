# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RumbleParams:
    """
    Parameters:
        target: Target intensity for the rumble.
        period: Time period between vibrations (in ms).
        magnitude: Amplitude of the rumble.
        length: Duration of the rumble effect (in seconds).
        delay: Delay before the rumble effect starts (in seconds).
        attack_length: Duration of the initial intensity ramp-up.
        attack_level: Level of intensity during the ramp-up.
        fade_length: Duration of the intensity ramp-down.
        fade_level: Level of intensity during the ramp-down.
        direction: Direction of the rumble effect.
    """

    target: float = 0
    period: float = 25
    magnitude: float = 24576
    length: float = 2
    delay: float = 0
    attack_length: float = 256
    attack_level: float = 0
    fade_length: float = 256
    fade_level: float = 0
    direction: float = 16384

    def __post_init__(self) -> None:
        if self.magnitude < 0:
            raise ValueError("Magnitude must be non-negative.")
        if self.length <= 0:
            raise ValueError("Length must be greater than zero.")

    def __str__(self) -> str:
        """
        Custom string representation of the dataclass for easy debugging and printing.
        """
        return (
            f"RumbleParams(\n"
            f"  target={self.target},\n"
            f"  period={self.period},\n"
            f"  magnitude={self.magnitude},\n"
            f"  length={self.length},\n"
            f"  delay={self.delay},\n"
            f"  attack_length={self.attack_length},\n"
            f"  attack_level={self.attack_level},\n"
            f"  fade_length={self.fade_length},\n"
            f"  fade_level={self.fade_level},\n"
            f"  direction={self.direction}\n"
            f")"
        )


class Rumble:
    """
    A class to handle controller haptic feedback and rumbling effects.
    """

    def __init__(self) -> None:
        """Initialize the Rumble instance."""

    def rumble(self, params: RumbleParams) -> None:
        """Simulate a rumble effect on the controller."""
        logger.debug(f"Rumbling parameters: {params.__str__()}.")


def find_library(locations: list[str]) -> Optional[str]:
    """
    Attempts to load a library from the provided locations.

    Parameters:
        locations: List of paths to potential library files.

    Returns:
        The path of the first successfully loaded library,
        or None if none are found.
    """
    try:
        from ctypes import cdll
    except ImportError:
        logger.debug("Ctypes is unavailable.")
        return None

    for path in locations:
        try:
            cdll.LoadLibrary(path)
            logger.debug(f"Successfully loaded library from: {path}")
            return path
        except OSError:
            logger.debug(f"Failed to load library from path: {path}")
    return None
