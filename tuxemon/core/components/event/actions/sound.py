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

import logging

from core import tools
from core import prepare
from core.platform import mixer

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Sound(object):

    def play_sound(self, game, action):
        """Plays a sound from "resources/sounds/"

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: filename

        **Examples:**

        >>> action.__dict__
        {
            "type": "play_sound",
            "parameters": [
                "interface/NenadSimic_Click.ogg"
            ]
        }

        """
        filename = str(action.parameters[0])
        sound = tools.load_sound("sounds/" + filename)
        sound.play()


    def play_music(self, game, action):
        """Plays a music file from "resources/music/"

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: filename

        **Examples:**

        >>> action.__dict__
        {
            "type": "play_music",
            "parameters": [
                "147066_pokemon.ogg"
            ]
        }

        """
        filename = str(action.parameters[0])
        mixer.music.load(prepare.BASEDIR + "resources/music/" + filename)
        mixer.music.play(-1)

        # Keep track of what song we're currently playing
        game.current_music["status"] = "playing"
        game.current_music["song"] = filename


    def pause_music(self, game, action):
        """Pauses the current music playback

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: None

        **Examples:**

        >>> action.__dict__
        {
            "type": "play_music",
            "parameters": []
        }

        """

        mixer.music.pause()
        if game.current_music["song"]:
            game.current_music["status"] = "paused"
        else:
            logger.warning("Music cannot be paused, none is playing.")


    def fadeout_music(self, game, action):
        """Fades out the music over a set amount of time in milliseconds

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: time_milliseconds

        **Examples:**

        >>> action.__dict__
        {
            "type": "fadeout_music",
            "parameters": [
                "1000"
            ]
        }

        """

        time = int(action.parameters[0])
        mixer.music.fadeout(time)
        if game.current_music["song"]:
            game.current_music["status"] = "stopped"
        else:
            logger.warning("Music cannot be paused, none is playing.")
