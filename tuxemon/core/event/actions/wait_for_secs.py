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


class WaitForSecsAction(EventAction):
    """Pauses the event engine for n number of seconds.

    Valid Parameters: duration

    * duration (float): time in seconds for the event engine to wait for

    **Examples:**

    >>> action.__dict__
    {
        "type": "wait_for_secs",
        "parameters": [
            "2.0"
        ]
    }

    """
    name = "wait_for_secs"
    valid_parameters = [
        (float, 'seconds')
    ]

    def start(self):
        secs = self.parameters.seconds
        self.session.client.event_engine.state = "waiting"
        self.session.client.event_engine.wait = secs
