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


class RumbleAction(EventAction):
    """ Rumbles available controllers with rumble support

    Valid Parameters: duration,power

    * duration (float): time in seconds to rumble for
    * power (int): percentage of power to rumble. (1-100)
    """
    name = "rumble"
    valid_parameters = [
        (float, "duration"),
        (int, "power")
    ]

    def start(self):
        duration = float(self.parameters[0])
        power = int(self.parameters[1])

        min_power = 0
        max_power = 24576

        if power < 0:
            power = 0
        elif power > 100:
            power = 100

        magnitude = int((power * 0.01) * max_power)
        self.session.client.rumble.rumble(-1, length=duration, magnitude=magnitude)
