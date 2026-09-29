# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import os
from typing import Any

from tuxemon.rumble.libshake import DummyRumble, LibShakeRumble, Rumble
from tuxemon.rumble.patterns import get_pattern
from tuxemon.rumble.tools import RumbleParams, find_library

# Set up logging for the rumble manager.
logger = logging.getLogger(__name__)


class RumbleManager:
    def __init__(self) -> None:
        """
        The Rumble Manager automatically selects an available
        rumble backend and controls controller haptic feedback.
        """
        self.rumbler: Rumble
        self.backend: str | None = None

        # Get backend locations, allowing for dynamic configuration
        locations = os.getenv("RUMBLE_BACKEND_LOCATIONS", "").split(",") or [
            "libshake.so",
            "./libshake.so",
            "/usr/lib/libshake.so",
        ]

        # Attempt to locate the backend
        logger.info(f"Attempting to locate rumble backends in: {locations}")
        lib_shake = self.select_backend(locations)

        if lib_shake:
            logger.info("Using libShake as backend.")
            self.backend = "libShake"
            self.rumbler = LibShakeRumble(lib_shake)
        else:
            logger.warning("No backend available, using Rumble.")
            self.rumbler = DummyRumble()

    def rumble(self, params: RumbleParams) -> None:
        self.rumbler.rumble(params)

    def play_pattern(self, target: int, name: str, **kwargs: Any) -> None:
        sequence = get_pattern(name, **kwargs)
        self.rumbler.rumble_sequence(target, sequence)

    def update(self, dt: float) -> None:
        self.rumbler.update(dt)

    def select_backend(self, locations: list[str]) -> str | None:
        """
        Attempts to locate a backend library from the provided locations.
        """
        lib_shake = find_library(locations)
        if lib_shake:
            logger.debug(f"Found library at: {lib_shake}")
            return lib_shake
        else:
            logger.debug("No backend library found.")
            return None
