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

import logging

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Core(object):

    def set_variable(self, game, action):
        """Sets the key in the player.game_variables dictionary.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: variable_name:value

        **Examples:**

        >>> action
        ('set_variable', 'battle_won:yes', '4', 1)

        """

        # Get the player object from the game.
        player = game.player1

        # Split the variable into a key: value pair
        varlist = action[1].split(":")
        varkey = str(varlist[0])
        varvalue = str(varlist[1])

        # Append the game_variables dictionary with the key: value pair
        player.game_variables[varkey] = varvalue


    def dialog(self, game, action):
        """Opens a dialog window with text

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: text_to_display

        You may also use special variables in dialog events. Here is a list of available variables:

        * ${{name}} - The current player's name.

        **Examples:**

        >>> action
        ('dialog', 'Red:\\n This is some dialog!', '3', 1)

        """

        text = str(action[1])
        text = text.replace("${{name}}", game.player1.name)
        logger.info("Dialog window opened")

        # Open a dialog window in the current scene.
        if not game.current_state.dialog_window.visible:
            game.current_state.dialog_window.visible = True
            game.current_state.dialog_window.text = text


    def rumble(self, game, action):
        """Rumbles available controllers with rumble support

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: duration,power

        * duration (float): time in seconds to rumble for
        * power (int): percentage of power to rumble. (1-100)

        **Examples:**

        >>> action
        ('rumble', '2,100', '3', 1)

        """

        duration = float(action[1].split(',')[0])
        power = int(action[1].split(',')[1])

        min_power = 0
        max_power = 24576

        if power < 0:
            power = 0
        elif power > 100:
            power = 100

        magnitude = int((power * 0.01) * max_power)
        game.rumble.rumble(-1, length=duration, magnitude=magnitude)


    def wait_for_secs(self, game, action):
        """Pauses the event engine for n number of seconds.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: duration

        * duration (float): time in seconds for the event engine to wait for

        **Examples:**

        >>> action
        ('wait_for_secs', '2.0')

        """
        secs = float(action[1])
        game.event_engine.state = "waiting"
        game.event_engine.wait = secs


    def wait_for_input(self, game, action):
        """Pauses the event engine until specified button is pressed

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: button

        * button (str): pygame key to wait for

        **Examples:**

        >>> action
        ('wait_for_input', 'K_RETURN')

        """
        button = str(action[1])
        game.event_engine.state = "waiting for input"
        game.event_engine.wait = 2
        game.event_engine.button = button

    def change_state(self, game, action):

        """Pauses the event engine until specified button is pressed

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: button

        * button (str): pygame key to wait for

        **Examples:**

        >>> action
        ('change_state', 'MAIN_MENU')

        """
        # Handle if networking is not supported and the PC is trying to be
        # accessed.
        if action[1] == "PC":
            if not game.imports["networking"].networking:
                message = "Networking is not supported on your system"
                self.dialog(game, (action[0], message))
                return

        # Don't override previous state if we are still in the state.
        if game.state_name != action[1]:
            game.push_state(action[1])
