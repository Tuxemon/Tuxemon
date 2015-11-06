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

from core import prepare
from core.components import map
from core.components import player
from core.components import pyganim
from core.components import item
from core.components import db
from core.components import monster
from core.components import ai
from core.components import plugin

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.event successfully imported")


class EventEngine(object):
    """A class for the event engine. The event engine checks to see if a group of conditions have
    been met and then executes a set of actions.

    """
    def __init__(self):

        # Load all the available conditions and actions as plugins.
        condition_plugins = plugin.load_directory(prepare.BASEDIR + "core/components/event/conditions")
        self.conditions = plugin.get_available_methods(condition_plugins)
        action_plugins = plugin.load_directory(prepare.BASEDIR + "core/components/event/actions")
        self.actions = plugin.get_available_methods(action_plugins)

        self.name = "Event"
        self.current_map = None
        self.state = "running"
        self.timer = 0.0
        self.wait = 0.0
        self.button = None


    def check_conditions(self, game, dt):
        """Checks a list of conditions to see if any of them have been met.

        :param game: The main game object that contains all the game's variables.
        :param game.event_conditions: The multi-dimensional list of conditions to check for. See
            :py:func:`core.components.map.Map.loadevents` to see the format of the list.
        :param dt: Amount of time passed in seconds since last frame.

        :type game: core.tools.Control
        :type game.event_conditions: List
        :type dt: Float

        :rtype: None
        :returns: None

        """

        if self.state == "running":
            for e in game.events:
                should_run = True

                # If any conditions fail, the event should not be run
                for cond in e['conds']:
                    # Conditions have so-called "operators".  If a condition's operator == "is" then
                    # the condition should be processed as usual.
                    # However, if the condition != "is", the result should be inverted.
                    # The following line implements this.
                    # I am not satisfied with the clarity of this line, so if anyone can express this better,
                    # please change it.
                    if not self.state == "running":
                        return
                    check_condition = self.conditions[cond['type']]['method']
                    should_run = (check_condition(game, cond) == (cond['operator'] == 'is'))
                    if not should_run:
                        break

                if should_run:
                    self.execute_action(e['acts'], game)

        elif self.state == "waiting":
            if self.timer >= self.wait:
                self.state = "running"
                self.timer = 0.0
            else:
                self.timer += dt
                logger.debug("Waiting %s seconds to resume event engine..." % str(self.wait - self.timer))

        elif self.state == "waiting for input":
            if not self.button:
                self.state = "running"
                return

            # Get the keys pressed from the game.
            events = game.key_events

            # Loop through each event
            for event in events:
                # NOTE: getattr on pygame is a little dangerous. We should sanitize input.
                if self.button and event.type == pygame.KEYUP and event.key == getattr(pygame, self.button):
                    self.state = "running"
                    self.button = None


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

        # Loop through the list of actions and execute them
        for action in action_list:

            # Call the method listed and return the modified event data
            try:
                self.actions[action[0]]["method"](game, action)
                #getattr( self.action, str(action[0]))(game, action)
            except Exception, message:
                error = 'Error: Action method "%s" not implemented' % str(action[0])
                logger.error(error)
                logger.error(message)
                traceback.print_exc()
