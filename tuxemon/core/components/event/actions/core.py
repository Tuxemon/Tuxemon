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
from yapsy.IPlugin import IPlugin

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Core(IPlugin):

    def set_variable(self, game, action):
        """Sets the key in the player.game_variables dictionary.
            
        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters
            
        :type game: core.tools.Control
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
            
        :type game: core.tools.Control
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
        if not game.state.dialog_window.visible:
            game.state.dialog_window.visible = True
            game.state.dialog_window.text = text
    
    
