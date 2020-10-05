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
from tuxemon.core.platform import mixer

logger = logging.getLogger(__name__)


class PauseMusicAction(EventAction):
    """Pauses the current music playback

    Valid Parameters: None
    """
    name = "pause_music"
    valid_parameters = []

    def start(self):
        mixer.music.pause()
        if self.session.client.current_music["song"]:
            self.session.client.current_music["status"] = "paused"
        else:
            logger.warning("Music cannot be paused, none is playing.")
