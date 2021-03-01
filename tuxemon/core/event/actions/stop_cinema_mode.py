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


class StopCinemaModeAction(EventAction):
    """Stops cinema mode by animating moving black bars to back to the normal aspect ratio.
    """
    name = "stop_cinema_mode"
    valid_parameters = []

    def start(self):
        world = self.session.client.current_state
        if world.cinema_state == "on":
            logger.info("Turning off cinema mode")
            world.cinema_state = "turning off"
