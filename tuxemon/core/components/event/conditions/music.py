#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
from __future__ import absolute_import

from core.platform import mixer


class Music(object):

    def music_playing(self, game, condition):
        """Checks to see if a particular piece of music is playing or not.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: music_filename

        **Examples:**

        >>> condition.__dict__
        {
            "type": "music_playing",
            "parameters": [
                "479403_its-a-unix-system.ogg"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        song = condition.parameters[0]

        # currently no way to query the names of states in the state control stack.
        # so we find names here.  possibly might make api to do this later.
        names = {i.name for i in game.active_states}
        combat_states = {"FlashTransition", "CombatState"}

        # means "if any element of combat_states is in names"
        if not names.isdisjoint(combat_states):
            return True

        if game.current_music["song"] == song and mixer.music.get_busy():
            return True
        else:
            return False

