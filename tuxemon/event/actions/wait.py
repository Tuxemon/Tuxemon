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

from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final


class WaitActionParameters(NamedTuple):
    seconds: float


@final
class WaitAction(EventAction[WaitActionParameters]):
    """Blocks event chain for some time

    Valid Parameters: duration

    * duration (float): time in seconds to wait for
    """

    name = "wait"
    param_class = WaitActionParameters

    # TODO: use event loop time, not wall clock
    def start(self) -> None:
        self.finish_time = time.time() + self.parameters.seconds

    def update(self) -> None:
        if time.time() >= self.finish_time:
            self.stop()
