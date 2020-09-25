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

import logging
from contextlib import contextmanager
from textwrap import dedent

from lxml import etree

from tuxemon.constants import paths
from tuxemon.core import plugin
from tuxemon.core import prepare
from tuxemon.core.platform.const import buttons

logger = logging.getLogger(__name__)


class RunningEvent:
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
    __slots__ = ('map_event', 'context', 'action_index', 'current_action', 'current_map_action')

    def __init__(self, map_event):
        self.map_event = map_event
        self.context = dict()
        self.action_index = 0
        self.current_action = None
        self.current_map_action = None

    def get_next_action(self):
        """ Get the next action to execute, if any

        Returns MapActions, which are just data from the map, not live objects

        None will be returned if the MapEvent is finished

        :rtype: tuxemon.core.event.MapAction
        """
        # if None, then make a new one
        try:
            action = self.map_event.acts[self.action_index]

        except IndexError:
            # reached end of list, remove event and move on
            logger.debug("map event actions finished")
            return

        return action


class EventEngine:
    """ A class for the event engine. The event engine checks to see if a group of
    conditions have been met and then executes a set of actions.

    Actions in the same MapEvent are not run concurrently, and they can be run over
    one or several frames.  Currently this engine is run in the context of a single map.

    Any actions or conditions executed on one map will be reset when the map is
    changed.

    """

    def __init__(self, session):
        self.session = session

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

        self.conditions = plugin.load_plugins(paths.CONDITIONS_PATH, "conditions")
        self.actions = plugin.load_plugins(paths.ACTIONS_PATH, "actions")

    def reset(self):
        """ Clear out running events.  Use when changing maps.

        :return:
        """
        self.running_events = dict()
        self.current_map = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

    def get_action(self, name, parameters=None):
        """ Get an action that is loaded into the engine

        A new instance will be returned each time

        Return None if action is not loaded

        :param parameters: list
        :type name: str

        :rtype: tuxemon.core.event.eventaction.EventAction

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
            return action(self.session, parameters)

    def get_condition(self, name):
        """ Get a condition that is loaded into the engine

        A new instance will be returned each time

        Return None if condition is not loaded

        :type name: str

        :rtype: tuxemon.core.event.eventcondition.EventCondition

        """
        # TODO: make generic
        try:
            condition = self.conditions[name]

        except KeyError:
            error = 'Error: EventCondition "{}" not implemented'.format(name)
            logger.error(error)

        else:
            return condition()

    def check_condition(self, cond_data, map_event):
        """ Check if condition is true of false

        Returns False if the condition is not loaded properly

        :type cond_data: tuxemon.core.event.MapCondition
        :type map_event: tuxemon.core.event.MapEvent
        :rtype: bool
        """
        with add_error_context(map_event, cond_data, self.session):
            map_condition = self.get_condition(cond_data.type)
            if map_condition is None:
                logger.debug('map condition "{}" is not loaded'.format(cond_data.type))
                return False

            result = map_condition.test(self.session, cond_data) == (cond_data.operator == 'is')
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
        [<class 'core.map.action'>, <class 'core.map.action'>]

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

        :type map_event: tuxemon.core.event.EventObject
        :return: None
        """
        # debugging mode is slower and will check all conditions
        if prepare.CONFIG.collision_map:
            # less optimal, debug
            started = 0
            conds = list()
            for cond in map_event.conds:
                if self.check_condition(cond, map_event):
                    conds.append((True, cond))
                    started += 1
                else:
                    conds.append((False, cond))

            if started == len(map_event.conds):
                self.start_event(map_event)

            self.partial_events.append(conds)

        else:
            # optimal, less debug
            if all(self.check_condition(cond, map_event) for cond in map_event.conds):
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
        if self.session.client.inits:
            self.process_map_events(self.session.client.inits)
            self.session.client.inits = list()

        # process any other events
        self.process_map_events(self.session.client.events)

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
                            with add_error_context(e.map_event, next_action, self.session):
                                action.start()

                            # save the action that is running
                            e.current_action = action

                # update the action
                action = e.current_action
                with add_error_context(e.map_event, e.current_map_action, self.session):
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
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        # has the player pressed the action key?
        if event.pressed and event.button == buttons.A:
            for map_event in self.session.client.interacts:
                self.process_map_event(map_event)

        return event


@contextmanager
def add_error_context(event, item, session):
    """
    :type event: tuxemon.core.event.EventObject
    :type item: tuxemon.core.event.MapCondition or core.event.MapAction
    :type session: tuxemon.core.session.Session
    :rtype None
    """
    try:
        yield
    except Exception:
        file_name = session.client.get_map_filepath()
        tree = etree.parse(file_name)
        event_node = tree.find("//object[@id='%s']" % event.id)
        if item.name is None:
            # It's an "interact" event, so no condition defined in the map
            msg = """
                Error in {file_name}
                {event}
                Line {line_number}
            """.format(
                file_name=file_name,
                event=etree.tostring(event_node).decode().split("\n")[0].strip(),
                line_number=event_node.sourceline,
            )
        else:
            # This is either a condition or an action
            child_node = event_node.find(".//property[@name='%s']" % (item.name))
            msg = """
                Error in {file_name}
                {event}
                    ...
                    {line}
                Line {line_number}
            """.format(
                file_name=file_name,
                event=etree.tostring(event_node).decode().split("\n")[0].strip(),
                line=etree.tostring(child_node).decode().strip(),
                line_number=child_node.sourceline,
            )
        print(dedent(msg))
        raise
