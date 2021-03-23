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
import uuid
from collections import defaultdict
from contextlib import contextmanager
from textwrap import dedent
from typing import List

from lxml import etree

from tuxemon import prepare
from tuxemon.event import MapCondition, EventObject, MapAction
from tuxemon.event.eventaction import EventAction
from tuxemon.event.eventcondition import EventCondition
from tuxemon.event.eventcontext import EventContext
from tuxemon.session import local_session, Session

logger = logging.getLogger(__name__)


class ActionList:
    __slots__ = (
        "session",
        "actions",
        "context",
        "index",
        "running_action",
    )

    def __init__(self, session, actions):
        self.session = session
        self.actions = actions
        self.context = None
        self.index = 0
        self.running_action = None


class EventEngine:
    """The event engine watches conditions and executes sets of actions """

    def __init__(self, conditions, actions):
        self.events = list()
        self.running_events = dict()
        self.conditions = dict()
        self.actions = dict()

        self.tags = defaultdict(list)
        self.messages = set()

        # TODO: remove this hack
        self.world = None
        self.map = None

        for item in actions:
            self.load_action(item)
        for item in conditions:
            self.load_condition(item)

    def load_action(self, action: EventAction):
        self.actions[action.name] = action

    def load_condition(self, condition: EventCondition):
        self.conditions[condition.name] = condition

    def load_events(self, events: List):
        for event in events:
            for event_condition in event.conds:
                condition = self.get_condition(event_condition.name)
                tag = condition.program(event_condition)
                if tag:
                    self.tags[tag].append(event)
                break  # this is a hack
            self.events.append(event)

    def get_action(self, name: str):
        try:
            return self.actions[name]
        except KeyError:
            error = f'Error: EventAction "{name}" could not be found'
            raise RuntimeError(error)

    def get_instanced_action(
        self, session: Session, name: str, parameters=None
    ) -> EventAction:
        """Get an action that is loaded into the engine
        A new instance will be returned each time
        """
        if parameters is None:
            parameters = list()
        action = self.get_action(name)
        context = EventContext(
            client=session.client,
            engine=self,
            map=self.map,
            player=session.player,
            session=session,
            world=session.world,
            name=name,
            parameters=parameters,
        )
        return action(context, parameters)

    def get_condition(self, name: str) -> EventCondition:
        """Get a condition that is loaded into the engine
        A new instance will be returned each time
        """
        try:
            condition = self.conditions[name]
        except KeyError:
            error = f'Error: EventCondition "{name}" could not be found'
            raise RuntimeError(error)
        else:
            return condition()

    def check_condition(self, session: Session, condition: MapCondition, map_event):
        """Check if condition is satisfied"""
        with add_error_context(map_event, condition, session):
            handler = self.get_condition(condition.name)
            result = handler.test(session, map_event, condition) == (
                condition.operator == "is"
            )
            logger.debug(f'map condition "{handler.name}": {result} ({condition})')
            return result

    def start_action(self, session, action_name, parameters=None, map=None):
        """ Begin execution of a single event"""
        event_id = str(uuid.uuid4())
        action_token = MapAction(action_name, parameters)
        actionlist = ActionList(session, [action_token])
        self.running_events[event_id] = actionlist
        return event_id

    def execute_action(self, session, action_name, parameters=None, map=None):
        """Load and execute an action.  Blocks until action is complete."""
        action = self.get_instanced_action(session, action_name, parameters)
        return action.execute()

    def start_event(self, session: Session, map_event: EventObject):
        """Begins execution of the action list.  Conditions are not checked."""
        if not map_event.conds and not map_event.acts:
            logger.debug(f"map event has no actions or conditions: {map_event}")
            return
        if map_event.id not in self.running_events:
            logger.debug(f"starting map event: {map_event}")
            actionlist = ActionList(session, map_event.acts)
            self.running_events[map_event.id] = actionlist

    def get_running_event(self, event_id):
        return self.running_events[event_id]

    def process_map_events(self, events):
        """Check conditions in a list or sequence and starts new actions"""
        for event in events:
            # TODO: support more sessions
            session = local_session

            if all(
                self.check_condition(session, cond, event) for cond in event.conds
            ):
                self.start_event(session, event)

    def set_message(self, message):
        self.messages.add(message)

    def update(self, dt: float):
        """Check all the MapEvents and start their actions if conditions are OK"""
        # self.check_conditions()

        session = local_session
        for message in self.messages:
            for event in self.tags[message]:
                if all(
                        self.check_condition(session, cond, event) for cond in event.conds
                ):
                    self.start_event(session, event)

        self.messages.clear()

        self.update_running_events(dt)

    def check_conditions(self):
        """Checks conditions.  If any are satisfied, start the MapActions

        Actions may be started during this function
        """
        self.process_map_events(self.events)

    def update_running_events(self, dt: float):
        """Update the events that are running"""
        finished_tasks = set()

        for task_id, actionlist in self.running_events.items():
            action = actionlist.running_action
            if action is None:
                name, parameters = actionlist.actions[actionlist.index]
                action = self.get_instanced_action(
                    actionlist.session,
                    name,
                    parameters,
                )
                actionlist.running_action = action
                action.start()
            else:
                action.update()

            if action.done:
                action.cleanup()
                actionlist.index += 1
                actionlist.running_action = None
                logger.debug(f"action finished: {action}")
                if actionlist.index == len(actionlist.actions):
                    finished_tasks.add(task_id)

        for task_id in finished_tasks:
            try:
                del self.running_events[task_id]
            except KeyError:
                # map changes or engine resets may cause this error
                pass


@contextmanager
def add_error_context(event, item, session):
    """
    :type event: tuxemon.event.EventObject
    :type item: tuxemon.event.MapCondition or event.MapAction
    :type session: tuxemon.session.Session
    """
    # with add_error_context(e.map_event, e.current_map_action, e.context):
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
                        event=etree.tostring(event_node)
                        .decode()
                        .split("\n")[0]
                        .strip(),
                        line=etree.tostring(child_node).decode().strip(),
                        line_number=child_node.sourceline,
                    )
        if msg:
            print(dedent(msg))

        raise
