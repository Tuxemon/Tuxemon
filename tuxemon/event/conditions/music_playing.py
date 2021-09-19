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
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform import mixer
from tuxemon.session import Session
from tuxemon.event import MapCondition


class MusicPlayingCondition(EventCondition):
    """
    Check to see if a particular piece of music is playing or not.

    Script usage:
        .. code-block::

            is music_playing <music_filename>

    Script parameters:
        music_filename: Name of the music.

    """

    name = "music_playing"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a particular piece of music is playing or not.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the chosen music is playing.

        """
        song = condition.parameters[0]

        # currently no way to query the names of states in the state game
        # stack.
        # so we find names here.  possibly might make api to do this later.
        names = {i.name for i in session.client.active_states}
        combat_states = {"FlashTransition", "CombatState"}

        # means "if any element of combat_states is in names"
        if not names.isdisjoint(combat_states):
            return True

        if session.client.current_music["song"] == song and mixer.music.get_busy():
            return True
        else:
            return False
