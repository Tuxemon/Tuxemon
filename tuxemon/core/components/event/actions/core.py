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
# Leif Theden <leif.theden@gmail.com>
#
from __future__ import absolute_import

import logging
from core.tools import open_dialog
from core.components.locale import translator
from functools import partial


# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self):
        # this is a potentially temporary solution to a problem with dialog chains
        self._dialog_chain_queue = list()
        self._menu = None

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
        text = text.replace(r"\n", "\n")

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

        >>> action.__dict__
        {
            "type": "set_variable",
            "parameters": [
                "battle_won:yes"
            ]
        }

        """

        # Get the player object from the game.
        player = game.player1

        # Split the variable into a key: value pair
        var_list = action.parameters[0].split(":")
        var_key = str(var_list[0])
        var_value = str(var_list[1])

        # Append the game_variables dictionary with the key: value pair
        player.game_variables[var_key] = var_value


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

        >>> action.__dict__
        {
            "type": "dialog",
            "parameters": [
                "Red:\\n This is some dialog!"
            ]
        }

        """

        text = str(action.parameters[0])
        text = self._replace_text(game, text)
        logger.info("Opening dialog window")

        # Open a dialog window in the current scene.
        open_dialog(game, [text])


    def translated_dialog(self, game, action):
        """Opens a dialog window with translated text according to the passed translation key. Parameters
        passed to the translation string will also be checked if a translation key exists.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: dialog_key,[var1=value1,var2=value2]

        You may also use special variables in dialog events. Here is a list of available variables:

        * ${{name}} - The current player's name.

        **Examples:**

        >>> action.__dict__
        {
            "type": "translated_dialog",
            "parameters": [
                "received_x",
                "name=Potion"
            ]
        }

        """
        trans = translator.translate
        key = str(action.parameters[0])
        replace_values = {}
        for param in action.parameters[1:]:
            values = param.split("=")
            param_key = values[0]
            param_value = values[1]

            # Check to see if param_value is translatable
            if translator.has_key(param_value):
                param_value = trans(param_value)

            replace_values[param_key] = self._replace_text(game, param_value)

        text = trans(key, replace_values)
        logger.info("Opening translated dialog window")

        # Open a dialog window in the current scene.
        open_dialog(game, [text])


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

        >>> action.__dict__
        {
            "type": "dialog_chain",
            "parameters": [
                "Red:\\n This is some dialog!"
            ]
        }

        """

        text = str(action.parameters[0])
        text = self._replace_text(game, text)
        logger.info("Opening chain dialog window")

        if text == "${{end}}":
            # Open a dialog window in the current scene.
            open_dialog(game, self._dialog_chain_queue, self._menu)
            self._dialog_chain_queue = list()
            self._menu = None
        else:
            self._dialog_chain_queue.append(text)


    def translated_dialog_chain(self, game, action):
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

        >>> action.__dict__
        {
            "type": "translated_dialog_chain",
            "parameters": [
                "received_x",
                "name=Potion"
            ]
        }

        """

        trans = translator.translate
        key = str(action.parameters[0])
        if key == "${{end}}":
            # Open a dialog window in the current scene.
            open_dialog(game, self._dialog_chain_queue, self._menu)
            self._dialog_chain_queue = list()
            self._menu = None
            return

        replace_values = {}
        for param in action.parameters[1:]:
            values = param.split("=")

            param_key = values[0]
            param_value = values[1]

            # Check to see if param_value is translatable
            if translator.has_key(param_value):
                param_value = trans(param_value)

            replace_values[param_key] = self._replace_text(game, param_value)

        text = trans(key, replace_values)
        logger.info("Opening translated chain dialog window")
        self._dialog_chain_queue.append(text)


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

        >>> action.__dict__
        {
            "type": "rumble",
            "parameters": [
                "2",
                "100"
            ]
        }

        """

        duration = float(action.parameters[0])
        power = int(action.parameters[1])

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

        >>> action.__dict__
        {
            "type": "wait_for_secs",
            "parameters": [
                "2.0"
            ]
        }

        """
        secs = float(action.parameters[0])
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

        >>> action.__dict__
        {
            "type": "wait_for_input",
            "parameters": [
                "K_RETURN"
            ]
        }

        """
        button = str(action.parameters[0])
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

        >>> action.__dict__
        {
            "type": "change_state",
            "parameters": [
                "MAIN_MENU"
            ]
        }

        """
        # Don't override previous state if we are still in the state.
        if game.state_name != action.parameters[0]:
            game.push_state(action.parameters[0])


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

        >>> action.__dict__
        {
            "type": "call_event",
            "parameters": [
                "2"
            ]
        }

        """
        event_engine = game.event_engine
        events = game.events

        for e in events:
            if e['id'] == int(action.parameters[0]):
                event_engine.execute_action(e['acts'], game)

    def dialog_choice(self, game, action):
        """Asks the player to make a choice.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: choice1:choice2,var_key
        """
        def set_variable(game, player, var_key, var_value):
            player.game_variables[var_key] = var_value
            game.pop_state()
            game.pop_state()

        # Get the player object from the game.
        player = game.player1

        var_list = action.parameters[0].split(":")
        var_menu = list()
        for val in var_list:
            var_menu.append((val, val, partial(set_variable, game=game, player=player, var_key=action.parameters[1], var_value=val)))
        self._menu = var_menu

    def translated_dialog_choice(self, game, action):
        """Asks the player to make a choice.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: choice1:choice2,var_key
        """
        def set_variable(game, player, var_key, var_value):
            player.game_variables[var_key] = var_value
            game.pop_state()
            game.pop_state()

        # Get the player object from the game.
        player = game.player1

        var_list = action.parameters[0].split(":")
        var_menu = list()
        for val in var_list:
            label = translator.translate(val).upper()
            var_menu.append((val, label, partial(set_variable, game=game, player=player, var_key=action.parameters[1], var_value=val)))
        self._menu = var_menu
