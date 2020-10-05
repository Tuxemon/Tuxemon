#
# Tuxemon
# Copyright (C) 2015, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# core.rumble Rumble library for Tuxemon
#
#

import logging

try:
    from ctypes import cdll
except:
    cdll = None
from tuxemon.core.rumble.tools import *

# Set up logging for the rumble manager.
logger = logging.getLogger(__name__)

class RumbleManager:
    def __init__(self):
        """The Rumble Manager automatically selects an available
        rumble backend and controls controller haptic feedback.
        """

        # Select the rumble backend to use.
        self.backend = None
        locations = ['libshake.so', './libshake.so', '/usr/lib/libshake.so']
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

