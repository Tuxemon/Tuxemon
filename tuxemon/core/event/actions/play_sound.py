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

from tuxemon.core import audio
from tuxemon.core.event.eventaction import EventAction


class PlaySoundAction(EventAction):
    """Plays a sound from "resources/sounds/"

    Valid Parameters: filename
    """
    name = "play_sound"
    valid_parameters = [
        (str, "filename"),
    ]

    def start(self):
        filename = self.parameters.filename
        sound = audio.load_sound(filename)
        sound.play()
