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

from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform import mixer


class MusicPlayingCondition(EventCondition):
    """Checks to see if a particular piece of music is playing or not."""

    name = "music_playing"

    def test(self, session, condition):
        """Checks to see if a particular piece of music is playing or not.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: music_filename
        """
        song = condition.parameters[0]

        # currently no way to query the names of states in the state game stack.
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
