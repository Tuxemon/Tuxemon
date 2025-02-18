# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

try:
    from ctypes import cdll
except ImportError:
    cdll = None
from tuxemon.rumble.tools import *

# Set up logging for the rumble manager.
logger = logging.getLogger(__name__)


class RumbleManager:
    def __init__(self) -> None:
        """The Rumble Manager automatically selects an available
        rumble backend and controls controller haptic feedback.
        """

        # Select the rumble backend to use.
        self.backend = None
        locations = ["libshake.so", "./libshake.so", "/usr/lib/libshake.so"]
        if not cdll:
            logger.debug("Ctypes is unavailable.")
            lib_shake = None
        else:
            lib_shake = find_library(locations)

        if lib_shake:
            logger.debug("Using libShake as backend.")
            from .libshake import LibShakeRumble

            self.backend = "libShake"
            self.rumbler = LibShakeRumble(lib_shake)
        else:
            logger.error("No rumble backends available.")
            self.rumbler = Rumble()
