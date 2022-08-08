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

from typing import NamedTuple, cast, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


class StartCinemaModeActionParameters(NamedTuple):
    pass


@final
class StartCinemaModeAction(EventAction[StartCinemaModeActionParameters]):
    """
    Start cinema mode by animating black bars to narrow the aspect ratio.

    Script usage:
        .. code-block::

            start_cinema_mode

    """

    name = "start_cinema_mode"
    param_class = StartCinemaModeActionParameters

    def start(self) -> None:
        world = cast(WorldState, self.session.client.current_state)
        if world.cinema_state == "off":
            world.cinema_state = "turning on"
