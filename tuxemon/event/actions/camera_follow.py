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

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class CameraFollow(EventAction):
    """Set camera to follow a game entity, including NPCs, Players, etc

    NOTE: only one camera is currently supported
    NOTE: single player only

    Valid Parameters: slug

    """

    name = "camera_follow"
    valid_parameters = [(str, "text")]

    def start(self):
        entity = get_npc(self.session, self.parameters[0])
        state = self.session.client.get_state_by_name("WorldState")
        state.follow(entity)
