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

from tuxemon.core.event.eventaction import EventAction


class TransitionTeleportAction(EventAction):
    """Combines the "teleport" and "screen_transition" actions to perform a teleport with a
    screen transition. Useful for allowing the player to go to different maps.

    Valid Parameters: map_name,coordinate_x,coordinate_y,transition_time_in_seconds

    **Examples:**

    >>> action.__dict__
    {
        "type": "transition_teleport",
        "parameters": [
            "taba_town.tmx",
            "5",
            "5",
            "2",
            "2"
        ]
    }

    """
    name = "transition_teleport"
    valid_parameters = [
        (str, "map_name"),
        (int, "x"),
        (int, "y"),
        (float, "transition_time"),
    ]

    def start(self):
        # Start the screen transition
        params = [self.parameters.transition_time]
        self.transition = self.session.client.event_engine.get_action("screen_transition", params)
        self.transition.start()

    def update(self):
        if not self.transition.done:
            self.transition.update()
        if self.transition.done:
            self.transition.cleanup()
            # set the delayed teleport
            self.session.client.event_engine.execute_action("delayed_teleport", self.raw_parameters[:-1])
            self.stop()
