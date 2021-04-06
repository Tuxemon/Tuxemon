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
from dataclasses import dataclass
from textwrap import dedent
from typing import List

from tuxemon.event import MapCondition, EventObject, MapAction
from tuxemon.event.eventaction import EventAction
from tuxemon.event.eventcondition import EventCondition
from tuxemon.event.eventcontext import EventContext
from tuxemon.session import local_session, Session

logger = logging.getLogger(__name__)


@dataclass
class ActionList:
    session: Session
    actions: List
    context: EventContext
    index: int
    running_action: callable


@dataclass
class LoadedAction:
    func: callable
    operator: str
    parameters: list


@dataclass
class LoadedCondition:
    condition: callable
    operator: bool
    map_condition: MapCondition


@dataclass
class LoadedEvent:
    id: str
    name: str
    rect: str
    conds: List[LoadedCondition]
    acts: List[LoadedAction]


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
        if action.name in self.actions:
            raise RuntimeError(action.name)
        self.actions[action.name] = action

    def load_condition(self, condition: EventCondition):
        if condition.name in self.conditions:
            raise RuntimeError(condition.name)
        instance = condition()
        self.conditions[condition.name] = instance

    def load_events(self, events: List[EventObject]):
        for event in events:
            conds = list()
            triggers = set()
            for event_condition in event.conds:
                condition = self.get_condition(event_condition)
                conds.append(condition)
                tag = condition.condition.program(event_condition)
                if tag:
                    triggers.add(tag)
            new_event = LoadedEvent(
                id=event.id,
                name=event.name,
                rect=event.rect,
                conds=conds,
                acts=event.acts,
            )
            self.events.append(new_event)
            for tag in triggers:
                self.tags[tag].append(new_event)

    def get_action(self, session: Session, name: str, parameters=None) -> EventAction:
        """Get an action that is loaded into the engine
        A new instance will be returned each time
        """
        if parameters is None:
            parameters = list()
        action = self.actions[name]
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

    def get_condition(self, data: MapCondition) -> LoadedCondition:
        """Get a condition that is loaded into the engine"""
        try:
            handler = self.conditions[data.name]
            condition = LoadedCondition(
                condition=handler, map_condition=data, operator=data.operator == "is"
            )
        except KeyError:
            error = f'Error: EventCondition "{data.name}" could not be found'
            raise RuntimeError(error)
        else:
            return condition

    def check_condition(self, session: Session, condition: LoadedCondition, map_event):
        """Check if condition is satisfied"""
        with add_error_context(map_event, condition, session):
            result = condition.condition.test(session, map_event, condition)
            result = result == condition.operator
            logger.debug(
                f'map condition "{condition.map_condition.name}": {result} ({condition})'
            )
            return result

    def start_action(self, session, action_name, parameters=None, map=None):
        """ Begin execution of a single event"""
        event_id = str(uuid.uuid4())
        action_token = MapAction(action_name, parameters)
        actionlist = ActionList(
            session=session,
            actions=[action_token],
            context=None,
            index=0,
            running_action=None,
        )
        self.running_events[event_id] = actionlist
        return event_id

    def execute_action(self, session, action_name, parameters=None, map=None):
        """Load and execute an action.  Blocks until action is complete."""
        action = self.get_action(session, action_name, parameters)
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

            if all(self.check_condition(session, cond, event) for cond in event.conds):
                self.start_event(session, event)

    def set_message(self, message):
        self.messages.add(message)

    def update(self, dt: float):
        """Check all the MapEvents and start their actions if conditions are OK"""
        session = local_session
        # self.process_map_events(self.events)
        for message in self.messages:
            for event in self.tags[message]:
                if all(
                    self.check_condition(session, cond, event) for cond in event.conds
                ):
                    self.start_event(session, event)

        self.messages.clear()
        self.update_running_events(dt)

    def update_running_events(self, dt: float):
        """Update the events that are running"""
        finished_tasks = set()

        for task_id, actionlist in self.running_events.items():
            action = actionlist.running_action
            if action is None:
                name, parameters = actionlist.actions[actionlist.index]
                action = self.get_action(
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
