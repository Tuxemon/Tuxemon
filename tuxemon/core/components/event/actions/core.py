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

    def _replace_text(self, game, text):
        """Replaces ${{var}} tiled variables with their in-game value.

        :param game: The main game object that contains all the game's variables.
        :param text: The text to replace.

        :type game: core.control.Control
        :type text: String

        :rtype: String
        :returns: Replaced string text with in-game values.

        **Examples:**

        >>> self._replace_text("${{name}} is running away!")
        'Red is running away!'

        """
        text = text.replace("${{name}}", game.player1.name)

        return text


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
        text = self._replace_text(game, text)
        logger.info("Dialog window opened")

        # Open a dialog window in the current scene.
        if not game.current_state.dialog_window.visible:
            game.current_state.dialog_window.visible = True
            game.current_state.dialog_window.text = text


    def dialog_chain(self, game, action):
        """Opens a chain of dialogs in order. Dialog chain must be ended with the ${{end}} keyword.

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
        * ${{end}} - Ends the dialog chain.

        **Examples:**

        >>> action
        ('dialog_chain', 'Red:\\n This is some dialog!', '3', 1)

        """

        text = str(action[1])
        text = self._replace_text(game, text)
        dialog_window = game.current_state.dialog_window

        # Do nothing if a dialog is already open
        if dialog_window.visible:
            return

        # If this is the end of the dialog chain, display the window.
        if "${{end}}" in text:
            logger.info("Dialog window opened")
            dialog_window.visible = True
            if len(dialog_window.dialog_stack) > 0:
                dialog_window.text = dialog_window.dialog_stack.pop(0)
            return

        # If this text is part of the dialog chain, add it to the dialog stack.
        if dialog_window.elapsed_time >= dialog_window.delay:
            logger.debug("Adding text to dialog stack: " + text)
            logger.debug("Seconds since last dialog: " + str(dialog_window.elapsed_time))
            dialog_window.dialog_stack.append(text)


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
        """Changes to the specified state.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: state_name

        * state_name (str): The state name to switch to.

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


    def call_event(self, game, action):
        """Executes the specified event's actions by id.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: event_id

        * event_id (int): The tmx id of the event to call.

        **Examples:**

        >>> action
        ('call_event', '2')

        """
        event_engine = game.event_engine
        events = game.events

        for e in events:
            if e['id'] == int(action[1]):
                event_engine.execute_action(e['acts'], game)
