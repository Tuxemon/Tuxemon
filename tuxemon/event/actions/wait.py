#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class WaitAction(EventAction):
    """
    Block event chain for some time.

    Script usage:
        .. code-block::

            wait <seconds>

    Script parameters:
        seconds: Time in seconds for the event engine to wait for.

    """

    name = "wait"
    seconds: float

    # TODO: use event loop time, not wall clock
    def start(self) -> None:
        self.finish_time = time.time() + self.seconds

    def update(self) -> None:
        if time.time() >= self.finish_time:
            self.stop()
