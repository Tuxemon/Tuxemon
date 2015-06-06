#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
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
#
# core.components.event Game events module.
#
#

import logging
import os
import pygame
import traceback
import random
import re
import pprint

from core.components import map
from core.components import player
from core.components import pyganim
from core.components import item
from core.components import db
from core.components import monster
from core.components import ai
from core.components import plugin

# Load all the available conditions and actions as plugins.
condition_plugins = plugin.load_directory("core/components/event/conditions")
condition_methods = plugin.get_available_methods(condition_plugins)
action_plugins = plugin.load_directory("core/components/event/actions")
action_methods = plugin.get_available_methods(action_plugins)

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.event successfully imported")


class EventEngine(object):
    """A class for the event engine. The event engine checks to see if a group of conditions have
    been met and then executes a set of actions.

    """
    def __init__(self):
        self.name = "Event"
        self.current_map = None
        self.conditions = condition_methods
        self.actions = action_methods


    def check_conditions(self, game):
        """Checks a list of conditions to see if any of them have been met.

        :param game: The main game object that contains all the game's variables.
        :param game.event_conditions: The multi-dimensional list of conditions to check for. See
            :py:func:`core.components.map.Map.loadevents` to see the format of the list.
        
        :type game: core.tools.Control
        :type game.event_conditions: List
    
        :rtype: None
        :returns: None
        
        """ 

        # Loop through the groups of conditions
        for condition_group in game.event_conditions:

            logger.debug("Current Condition Group: " + str(condition_group))
            
            # Keep track of whether or not all conditions in the group have been met
            group_met = False
            
            # Loop through each condition in a condition group
            for condition in condition_group:
                logger.debug(condition["type"] + " " + condition["operator"] + " " + condition["parameters"])

                if condition["type"] not in condition_methods:
                    error = 'Error: Condition method "%s" not implemented' % str(condition["type"])
                    logger.error(error)
                    group_met = False
                    break
                    
                # Call the method based on the type of condition we're checking for
                try:
                    condition_met = condition_methods[condition["type"]]["method"](game, condition)
                    if self.operator_check(condition, condition_met):
                        group_met = True
                    # If just one condition in the condition group isn't met then stop looping and
                    # go to the next group
                    else:
                        group_met = False
                        break
                except Exception, err:
                    logger.error(traceback.format_exc())

            # If all the conditions in the condition group were met, execute the action(s)
            # associated with it
            if group_met:
                action_list = self.current_map.loadactions(condition_group[0]["action_id"])
                logger.debug("All conditions met!")
                logger.debug(str(action_list))
                
                # Execute the action according to its action type
                self.execute_action(action_list, game) 
            else:
                logger.debug("Conditions not met!")
                
        
    def execute_action(self, action_list, game):
        """Executes a particular action in a list of actions.
        
        :param action_list: A list of actions fetched from the database. 
        :param game: The main game object that contains all the game's variables.
        
        :type action_list: List
        :type game: core.tools.Control

        Here is an example of what an action list might look like:

        >>> action_list
        [(u'teleport', u'example.map,1,1', 1, 1), (u'teleport', u'test.map,4,3', 2, 2)]
    
        :rtype: None
        :returns: None
        
        """ 
        
        logger.debug("Executing Action")

        # Sort the action list by the priority column so actions are executed in the correct
        # order. (e.g. priority 1 actions execute first)
        action_list.sort(key=lambda tup: tup[2])
        
        # Loop through the list of actions and execute them
        for action in action_list:
            
            # Call the method listed and return the modified event data
            try:
                action_methods[action[0]]["method"](game, action)
                #getattr( self.action, str(action[0]))(game, action) 
            except Exception, message:
                error = 'Error: Action method "%s" not implemented' % str(action[0])
                logger.error(error)
                logger.error(message)
                traceback.print_exc()


    def operator_check(self, condition, conditions_met):
        """Checks the condition operator to see if we need to meet these conditions or if we need
        to NOT meet these conditions. For example, if we do meet the conditions and we WANT to
        meet them, return true. If we meet the conditions but we DON'T WANT to meet them, 
        return false.

        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary. 
        :param conditions_met: A True/False value of whether or not the conditions were met.
        
        :type condition: Dictionary
        :type conditions_met: Boolean
    
        :rtype: Boolean
        :returns: True or False 
        
        """ 

        operator = condition["operator"].lower()
        if operator == "is" and conditions_met:
            return True
        elif operator == "is" and not conditions_met:
            return False
        elif operator == "is_not" and conditions_met:
            return False
        elif operator == "is_not" and not conditions_met:
            return True


