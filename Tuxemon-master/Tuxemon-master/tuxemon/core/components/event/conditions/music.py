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

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


class Music(object):

    def music_playing(self, game, condition):
        """Checks to see if a particular piece of music is playing or not.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.tools.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: music_filename

        **Examples:**

        >>> condition
        {'action_id': '7',
         'id': 7,
         'type': 'music_playing',
         'operator': 'is',
         'parameters': '479403_its-a-unix-system.ogg',
         'x': 0,
         'y': 0}

        """

        if (game.state_dict["WORLD"].start_battle_transition or
                game.state_dict["WORLD"].battle_transition_in_progress or
                game.state_name == "COMBAT" or game.state.done):
            return True

        if game.current_music["song"] == condition["parameters"] and mixer.music.get_busy():
            return True
        else:
            return False

