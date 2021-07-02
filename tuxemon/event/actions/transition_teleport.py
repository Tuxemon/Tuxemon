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
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final


class TransitionTeleportActionParameters(NamedTuple):
    map_name: str
    x: int
    y: int
    transition_time: float


@final
class TransitionTeleportAction(EventAction[TransitionTeleportActionParameters]):
    """Combines the "teleport" and "screen_transition" actions to perform a teleport with a
    screen transition. Useful for allowing the player to go to different maps.

    Valid Parameters: map_name,coordinate_x,coordinate_y,transition_time_in_seconds
    """

    name = "transition_teleport"
    param_class = TransitionTeleportActionParameters

    def start(self) -> None:
        # Start the screen transition
        params = [self.parameters.transition_time]
        self.transition = self.session.client.event_engine.get_action("screen_transition", params)
        self.transition.start()

    def update(self) -> None:
        if not self.transition.done:
            self.transition.update()
        if self.transition.done:
            self.transition.cleanup()
            # set the delayed teleport
            self.session.client.event_engine.execute_action("delayed_teleport", self.raw_parameters[:-1])
            self.stop()
