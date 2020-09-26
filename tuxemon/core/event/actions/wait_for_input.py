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


import logging

from tuxemon.core.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class WaitForInputAction(EventAction):
    """Pauses the event engine until specified button is pressed

    Valid Parameters: button

    * button (str): pygame key to wait for

    **Examples:**

    >>> action.__dict__
    {
        "type": "wait_for_input",
        "parameters": [
            "K_RETURN"
        ]
    }

    """
    name = "wait_for_input"
    valid_parameters = [
        (str, "button")
    ]

    def start(self):
        logger.warning("the wait_for_input action has been deprecated, please remove it from your scripts")
        self.session.client.event_engine.button = self.parameters.button
        self.session.client.event_engine.state = "waiting for input"
        self.session.client.event_engine.wait = 2
