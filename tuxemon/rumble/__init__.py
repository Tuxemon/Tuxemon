# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import os
from typing import Optional, Union

from tuxemon.rumble.tools import Rumble, find_library

from .libshake import LibShakeRumble

# Set up logging for the rumble manager.
logger = logging.getLogger(__name__)


class RumbleManager:
    def __init__(self) -> None:
        """
        The Rumble Manager automatically selects an available
        rumble backend and controls controller haptic feedback.
        """
        self.rumbler: Union[LibShakeRumble, Rumble]
        self.backend: Optional[str] = None

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
            self.rumbler = Rumble()

    def select_backend(self, locations: list[str]) -> Optional[str]:
        """
        Attempts to locate a backend library from the provided locations.
        """
        try:
            from ctypes import cdll
        except ImportError:
            logger.debug("Ctypes is unavailable.")
            return None

        lib_shake = find_library(locations)
        if lib_shake:
            logger.debug(f"Found library at: {lib_shake}")
            return lib_shake
        else:
            logger.debug("No backend library found.")
            return None
