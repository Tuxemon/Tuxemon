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
from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from textwrap import dedent

from lxml import etree

from tuxemon import plugin, prepare
from tuxemon.constants import paths
# from tuxemon.event.eventcontext import EventContext
from tuxemon.session import local_session

logger = logging.getLogger(__name__)


# TODO: rename this or resolve the issue with two classes called "eventcontext"
@dataclass
class EventContext:
    engine: EventEngine
    world: World
    session: Session
    client: LocalPygameClient
    player: Player
    map: TuxemonMap


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

    __slots__ = (
        "map_event",
        "session",
        "context",
        "action_index",
        "current_action",
        "current_map_action",
    )

    def __init__(self, session, map_event):
        self.session = session
        self.map_event = map_event
        self.context = dict()
        self.action_index = 0
        self.current_action = None
        self.current_map_action = None

    def get_next_action(self):
        """ Get the next action to execute, if any

        Returns MapActions, which are just data from the map, not live objects

        None will be returned if the MapEvent is finished

        :rtype: tuxemon.event.MapAction
        """
        try:
            action = self.map_event.acts[self.action_index]
        except IndexError:
            # reached end of list, remove event and move on
            logger.debug("map event actions finished")
            return
        return action

    def advance(self):
        self.action_index += 1


class EventEngine:
    """ A class for the event engine. The event engine checks to see if a group of
    conditions have been met and then executes a set of actions.

    Actions in the same MapEvent are not run concurrently, and they can be run over
    one or several frames.  Currently this engine is run in the context of a single map.

    The event engine checks to see if a group of conditions have been met
    and then executes a set of actions.

    Actions in the same MapEvent are not run concurrently, and they can be
    run over one or several frames.
    """

    def __init__(self, events):
        self.events = events
        self.conditions = dict()
        self.actions = dict()
        self.running_events = dict()
        self.partial_events = list()
        self.conditions = plugin.load_plugins(paths.CONDITIONS_PATH, "conditions")
        self.actions = plugin.load_plugins(paths.ACTIONS_PATH, "actions")

        # TODO: remove this hack
        self.world = None
        self.map = None

    def get_action(self, session, name, parameters=None):
        """ Get an action that is loaded into the engine

        A new instance will be returned each time

        :param tuxemon.session.Session session:
        :param str name:
        :param List parameters:
        :rtype: tuxemon.event.eventaction.EventAction
        """
        if parameters is None:
            parameters = list()
        try:
            action = self.actions[name]
        except KeyError:
            error = f'Error: EventAction "{name}" not implemented'
            raise RuntimeError(error)
        else:
            context = EventContext(
                engine=self,
                world=session.world,
                session=session,
                client=session.client,
                player=session.player,
                map=self.map,
            )
            return action(context, parameters)

    def get_condition(self, name):
        """ Get a condition that is loaded into the engine

        A new instance will be returned each time

        :param str name:
        :rtype: tuxemon.event.eventcondition.EventCondition
        """
        try:
            condition = self.conditions[name]
        except KeyError:
            error = f'Error: EventCondition "{name}" not implemented'
            raise RuntimeError(error)
        else:
            return condition()

    def check_condition(self, session, condition, map_event):
        """ Check if condition is true or false

        :param tuxemon.session.Session session:
        :param tuxemon.event.MapCondition condition:
        :param tuxemon.event.MapEvent map_event:
        :rtype: bool
        """
        with add_error_context(map_event, condition, session):
            handler = self.get_condition(condition.name)
            result = handler.test(session, map_event, condition) == (condition.operator == "is")
            logger.debug(f'map condition "{handler.name}": {result} ({condition})')
            return result

    def execute_action(self, session, action_name, parameters=None, map=None):
        """ Load and execute an action

        This will cause the game to hang if an action waits on game changes

        :param str action_name:
        :param Optional[Tuple] parameters:
        :rtype: bool
        """
        if parameters is None:
            parameters = list()

        action = self.get_action(session, action_name, parameters)
        if action is None:
            logger.debug(f'map action "{action_name}" is not loaded')

        return action.execute()

    def start_event(self, session, map_event):
        """ Begins execution of action list.  Conditions are not checked.

        :param tuxemon.session.Session session:
        :param tuxemon.event.EventObject map_event:
        """
        # the event id is used to make sure multiple copies of the same event are not
        # started.  If not checked, then the game would freeze while it tries to run
        # unlimited copies of the same event, forever.
        if map_event.id not in self.running_events:
            logger.debug(f"starting map event: {map_event}")
            logger.debug("Executing action list")
            logger.debug(map_event)
            token = RunningEvent(session, map_event)
            self.running_events[map_event.id] = token

    def process_map_event(self, map_event):
        """ Check the conditions of an event, and execute actions if all conditions are valid

        Actions will be started, but may finish much later.

        :param tuxemon.event.EventObject map_event:
        """
        # TODO: support more sessions
        session = local_session

        # debugging mode is slower and will check all conditions
        if prepare.CONFIG.collision_map:
            # less optimal, debug
            started = 0
            conds = list()
            for cond in map_event.conds:
                if self.check_condition(session, cond, map_event):
                    conds.append((True, cond))
                    started += 1
                else:
                    conds.append((False, cond))

            if started == len(map_event.conds):
                self.start_event(session, map_event)

            self.partial_events.append(conds)

        else:
            # optimal, less debug
            if all(self.check_condition(session, cond, map_event) for cond in map_event.conds):
                self.start_event(session, map_event)

    def process_map_events(self, events):
        """ Check conditions in a list or sequence.  Start actions

        Simple now, may become more complex

        :param List events:
        """
        for event in events:
            self.process_map_event(event)

    def update(self, dt):
        """ Check all the MapEvents and start their actions if conditions are OK

        :param Float dt: Amount of time passed in seconds since last frame.
        """
        self.partial_events = list()
        # NOTE: there is a potential bug here; if/when a condition here starts
        # a new action, that action will be updated immediately after with a time
        # delta.  the dt for new actions should be essentially 0, but in this case
        # it will be some value greater.
        self.check_conditions()
        self.update_running_events(dt)

    def check_conditions(self):
        """ Checks conditions.  If any are satisfied, start the MapActions

        Actions may be started during this function
        """
        self.process_map_events(self.events)

    def update_running_events(self, dt):
        """ Update the events that are running

        :param Float dt: Amount of time passed in seconds since last frame.
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
                        action = self.get_action(e.session, next_action.type, next_action.parameters, )

                        if action is None:
                            # action was not loaded, so, break?  raise exception, idk
                            # TODO: raise custom exception instead of None return?
                            # TODO: decide what to do for actions not loaded
                            logger.debug("action is not loaded!")
                            to_remove.add(i)
                            break

                        else:
                            # start the action
                            with add_error_context(e.map_event, next_action, e.context):
                                action.start()

                            # save the action that is running
                            e.current_action = action

                # update the action
                action = e.current_action
                with add_error_context(e.map_event, e.current_map_action, e.context):
                    action.update()

                if action.done:
                    # action finished, so continue and do the next one, if available
                    action.cleanup()
                    e.action_index += 1
                    e.current_action = None
                    logger.debug(f"action finished: {action}")

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

        :param tuxemon.input.PlayerInput event:
        :rtype: Optional[input.PlayerInput]
        """
        # has the player pressed the action key?
        # if event.pressed and event.button == buttons.A:
        #     for map_event in self.world.interacts:
        #         self.process_map_event(map_event)
        #
        return event


@contextmanager
def add_error_context(event, item, session):
    """
    :type event: tuxemon.event.EventObject
    :type item: tuxemon.event.MapCondition or event.MapAction
    :type session: tuxemon.session.Session
    """
    try:
        yield
    except Exception:
        raise
        file_name = session.client.get_map_filepath()
        tree = etree.parse(file_name)
        event_node = tree.find("//object[@id='%s']" % event.id)
        msg = None
        if event_node:
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
                if child_node:
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
        if msg:
            print(dedent(msg))

        raise
