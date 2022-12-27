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

from dataclasses import dataclass, field
from typing import Optional, final

from tuxemon.event.actions.screen_transition import ScreenTransitionAction
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class TransitionTeleportAction(EventAction):
    """
    Combines the "teleport" and "screen_transition" actions.

    Perform a teleport with a screen transition. Useful for allowing the player
    to go to different maps.

    Script usage:
        .. code-block::

            transition_teleport <map_name>,<x>,<y>,<transition_time>

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
        transition_time: Transition time in seconds.

    """

    name = "transition_teleport"
    map_name: str
    x: int
    y: int
    transition_time: Optional[float] = None
    transition: Optional[ScreenTransitionAction] = field(
        default=None, init=False
    )

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        if world.delayed_teleport:
            self.stop()
            return

        # Start the screen transition
        self.transition = self.session.client.event_engine.get_action(
            "screen_transition",
            [self.transition_time],
        )
        assert self.transition
        self.transition.start()

    def update(self) -> None:
        if self.done:
            return

        assert self.transition

        if not self.transition.done:
            self.transition.update()
        if self.transition.done:
            self.transition.cleanup()
            # set the delayed teleport
            self.session.client.event_engine.execute_action(
                "delayed_teleport",
                (self.map_name, self.x, self.y),
            )
            self.stop()
