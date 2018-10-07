# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
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
import os.path

import pygame

from tuxemon.constants import paths
from tuxemon.core import prepare
from tuxemon.core.components import plugin

logger = logging.getLogger(__name__)


class RunningEvent(object):
    """ Manage MapEvents that are used during gameplay

    Running events are considered to have all conditions satisfied
    Once started, they will eventually execute all actions of the MapEvent
    RunningEvents do not preserve state between calls or maps

    RunningEvents have an action_index
    The action_index is the index of the action list of the action currently running
    The current_action attribute is the instance of the running action

    Actions being managed by the RunningEvent class can share information
    using the context dictionary.
    """
    __slots__ = ['map_event', 'context', 'action_index', 'current_action']

    def __init__(self, map_event):
        self.map_event = map_event
        self.context = dict()
        self.action_index = 0
        self.current_action = None

    def get_next_action(self):
        """ Get the next action to execute, if any

        Returns MapActions, which are just data from the map, not live objects

        None will be returned if the MapEvent is finished

        :rtype: core.components.event.MapAction
        """
        # if None, then make a new one
        try:
            action = self.map_event.acts[self.action_index]

        except IndexError:
            # reached end of list, remove event and move on
            logger.debug("map event actions finished")
            return

        return action


class EventEngine(object):
    """ A class for the event engine. The event engine checks to see if a group of
    conditions have been met and then executes a set of actions.

    Actions in the same MapEvent are not run concurrently, and they can be run over
    one or several frames.  Currently this engine is run in the context of a single map.

    Any actions or conditions executed on one map will be reset when the map is
    changed.

    """

    def __init__(self, game):
        self.game = game

        self.conditions = dict()
        self.actions = dict()
        self.running_events = dict()
        self.name = "Event"
        self.current_map = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

        # debug
        self.partial_events = list()

        # TODO: maybe move the stuff below to the game/control class?

        # Load all the available conditions
        path = os.path.join(paths.BASEDIR, "core/components/event/conditions")
        self.load_plugins(path, "conditions")

        # Load all the available actions
        path = os.path.join(paths.BASEDIR, "core/components/event/actions")
        self.load_plugins(path, "actions")

    def reset(self):
        """ Clear out running events.  Use when changing maps.

        :return:
        """
        self.running_events = dict()
        self.current_map = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

    def load_plugins(self, path, category):
        """ Load classes and store for use later

        If there are plugins with the same name loaded, then the
        newest one will be used, and a debug message printed.

        :param path: will be searched for plugin classes
        :param category: "actions" or "conditions"

        :return: None
        """
        assert category in ("actions", "conditions")

        classes = self.load_classes_from_plugins(path, category)
        storage = getattr(self, category)
        storage.update(classes)

    @staticmethod
    def load_classes_from_plugins(path, category="plugin"):
        """ Load classes using plugin system

        :param path: where plugins are stored
        :param category: optional string for debugging info

        :type path: str
        :type category: str

        :rtype: dict
        """
        classes = dict()
        plugins = plugin.load_directory(path)

        for cls in plugin.get_available_classes(plugins):

            # TODO: enforce a template for plugins; make this generic
            name = getattr(cls, "name", None)
            if name is None:
                logger.error("found incomplete {}: {}".format(category, cls.__name__))
                continue
            classes[name] = cls
            logger.info("loaded {}: {}".format(category, cls.name))

        return classes

    def get_action(self, name, parameters=None):
        """ Get an action that is loaded into the engine

        A new instance will be returned each time

        Return None if action is not loaded

        :param parameters: list
        :type name: str

        :rtype: core.components.event.eventaction.EventAction

        """
        # TODO: make generic
        if parameters is None:
            parameters = list()

        try:
            action = self.actions[name]

        except KeyError:
            error = 'Error: EventAction "{}" not implemented'.format(name)
            logger.error(error)

        else:
            return action(self.game, parameters)

    def get_condition(self, name):
        """ Get a condition that is loaded into the engine

        A new instance will be returned each time

        Return None if condition is not loaded

        :type name: str

        :rtype: core.components.event.eventcondition.EventCondition

        """
        # TODO: make generic
        try:
            condition = self.conditions[name]

        except KeyError:
            error = 'Error: EventCondition "{}" not implemented'.format(name)
            logger.error(error)

        else:
            return condition()

    def check_condition(self, cond_data):
        """ Check if condition is true of false

        Returns False if the condition is not loaded properly

        :type cond_data: core.components.event.MapCondition
        :rtype: bool
        """
        map_condition = self.get_condition(cond_data.type)
        if map_condition is None:
            logger.debug('map condition "{}" is not loaded'.format(cond_data.type))
            return False

        result = map_condition.test(self.game, cond_data) == (cond_data.operator == 'is')
        logger.debug('map condition "{}": {} ({})'.format(map_condition.name, result, cond_data))
        return result

    def execute_action(self, action_name, parameters=None):
        """ Load and execute an action

        This will cause the game to hang if an action waits on game changes

        :type action_name: str
        :type parameters: tuple

        :rtype: bool
        """
        if parameters is None:
            parameters = list()

        action = self.get_action(action_name, parameters)
        if action is None:
            logger.debug('map action "{}" is not loaded'.format(action_name))

        return action.execute()

    def start_event(self, map_event):
        """ Begins execution of action list.  Conditions are not checked.

        :param map_event:
        :type map_event: EventObject

        Here is an example of what an action list might look like:

        >>> map_event
        [<class 'core.components.map.action'>, <class 'core.components.map.action'>]

        :rtype: None
        :returns: None

        """
        # the event id is used to make sure multiple copies of the same event are not
        # started.  If not checked, then the game would freeze while it tries to run
        # unlimited copies of the same event, forever.
        if map_event.id not in self.running_events:
            logger.debug("starting map event: {}".format(map_event))
            logger.debug("Executing action list")
            logger.debug(map_event)
            token = RunningEvent(map_event)
            self.running_events[map_event.id] = token

    def process_map_event(self, map_event):
        """ Check the conditions of an event, and execute actions if all conditions are valid

        Actions will be started, but may finish much later.

        :type map_event: core.components.event.EventObject
        :return: None
        """
        # debugging mode is slower and will check all conditions
        if prepare.CONFIG.collision_map:
            # less optimal, debug
            started = 0
            conds = list()
            for cond in map_event.conds:
                if self.check_condition(cond):
                    conds.append((True, cond))
                    started += 1
                else:
                    conds.append((False, cond))

            if started == len(map_event.conds):
                self.start_event(map_event)

            self.partial_events.append(conds)

        else:
            # optimal, less debug
            if all(map(self.check_condition, map_event.conds)):
                self.start_event(map_event)

    def process_map_events(self, events):
        """ Check conditions in a list or sequence.  Start actions

        Simple now, may become more complex

        :type events: list
        :return: None
        """
        for event in events:
            self.process_map_event(event)

    def update(self, dt):
        """ Check all the MapEvents and start their actions if conditions are OK

        :param dt: Amount of time passed in seconds since last frame.
        :type dt: float

        :rtype: None
        """
        # debug
        self.partial_events = list()
        self.check_conditions()
        self.update_running_events(dt)

    def check_conditions(self):
        """ Checks conditions.  If any are satisfied, start the MapActions

        Actions may be started during this function

        :rtype: None
        :returns: None

        """
        # do the "init" events.  this will be done just once
        # TODO: find solution that doesn't nuke the init list
        # TODO: make event engine generic, so can be used in global scope, not just maps
        if self.game.inits:
            self.process_map_events(self.game.inits)
            self.game.inits = list()

        # process any other events
        self.process_map_events(self.game.events)

    def update_running_events(self, dt):
        """ Update the events that are running

        :param dt: Amount of time passed in seconds since last frame.
        :type dt: float

        :rtype: None
        """
        to_remove = set()

        # Loop through the list of actions and update them
        for i, e in self.running_events.items():
            while 1:
                """
                * if RunningEvent is currently running an action, then continue to do so
                * if not, attempt to get the next queued action
                * if no queued action, do not check the RunningEvent next frame
                * if there is an action, then update it
                * if action is finished, then clear the pointer to the action and inc. the index, cleanup
                * RunningEvent will be checked next frame
                
                This loop will execute as many actions as possible for every MapEvent
                For example, some actions like set_variable do not require several frames,
                so all of them will be processed this frame.
                
                If an action is not finished, then this loop breaks and will check another
                RunningEvent, but the position in the action list is remembered and will be restored.
                """
                if e.current_action is None:
                    next_action = e.get_next_action()

                    if next_action is None:
                        # no next action, so remove the running event
                        to_remove.add(i)
                        break

                    else:
                        # got an action, so start it
                        action = self.get_action(next_action.type, next_action.parameters)

                        if action is None:
                            # action was not loaded, so, break?  raise exception, idk
                            # TODO: raise custom exception instead of None return?
                            # TODO: decide what to do for actions not loaded
                            logger.debug("action is not loaded!")
                            to_remove.add(i)
                            break

                        else:
                            # start the action
                            action.start()

                            # save the action that is running
                            e.current_action = action

                # update the action
                action = e.current_action
                action.update()

                if action.done:
                    # action finished, so continue and do the next one, if available
                    action.cleanup()
                    e.action_index += 1
                    e.current_action = None
                    logger.debug("action finished: {}".format(action))

                else:
                    # action didn't finish, so move on to next RunningEvent
                    break

        for i in to_remove:
            try:
                del self.running_events[i]
            except KeyError:
                # map changes or engine resets may cause this error
                pass

    def process_event(self, event):
        """ Process a pygame event

        :type event: pygame.Event
        :rtype: pygame.Ecent
        """
        # TODO: getattr on pygame is a little dangerous. We should sanitize input.
        if self.button and event.type == pygame.KEYUP and event.key == getattr(pygame, self.button):
            logger.debug("got button")
            self.button = None

        # has the player pressed the action key?
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            for map_event in self.game.interacts:
                self.process_map_event(map_event)

        return event
