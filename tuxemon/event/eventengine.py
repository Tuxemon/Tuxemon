# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Iterable, Sequence
from contextlib import contextmanager
from textwrap import dedent
from typing import Any, Optional, Union

from tuxemon import plugin, prepare
from tuxemon.constants import paths
from tuxemon.event import EventObject, MapAction, MapCondition
from tuxemon.event.eventaction import EventAction
from tuxemon.event.eventcondition import EventCondition
from tuxemon.map import TuxemonMap
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class RunningEvent:
    """
    Manage MapEvents that are used during gameplay.

    Running events are considered to have all conditions satisfied.
    Once started, they will eventually execute all actions of the MapEvent.
    RunningEvents do not preserve state between calls or maps.

    RunningEvents have an action_index.
    The action_index is the index of the action list of the action currently
    running.
    The current_action attribute is the instance of the running action.

    Actions being managed by the RunningEvent class can share information
    using the context dictionary.

    Parameters:
        map_event: Event defined in the map containing the information
            about the actions.

    """

    __slots__ = (
        "map_event",
        "context",
        "action_index",
        "current_action",
        "current_map_action",
        "cancelled",
    )

    def __init__(self, map_event: EventObject) -> None:
        self.map_event = map_event
        self.context: dict[str, Any] = dict()
        self.action_index = 0
        self.current_action: Optional[EventAction] = None
        self.current_map_action = None
        self.cancelled = False

    def get_next_action(self) -> Optional[MapAction]:
        """
        Get the next action to execute, if any.

        Returns MapActions, which are just data from the map, not live objects.

        ``None`` will be returned if the MapEvent is finished.

        Returns:
            Next action to execute. ``None`` if there isn't one.

        """
        # if None, then make a new one
        try:
            action = self.map_event.acts[self.action_index]

        except IndexError:
            # reached end of list, remove event and move on
            logger.debug("map event actions finished")
            return None

        return action

    def advance(self) -> None:
        self.action_index += 1

    def cancel(self) -> None:
        """Cancels the event."""
        self.cancelled = True


class EventEngine:
    """
    A class for the event engine. The event engine checks to see if a group of
    conditions have been met and then executes a set of actions.

    Actions in the same MapEvent are not run concurrently, and they can be run
    over one or several frames. Currently this engine is run in the context of
    a single map.

    Any actions or conditions executed on one map will be reset when the map is
    changed.

    Parameters:
        session: Object containing the session information.

    """

    def __init__(self, session: Session) -> None:
        self.session = session

        self.running_events: dict[int, RunningEvent] = dict()
        self.name = "Event"
        self.current_map: Optional[TuxemonMap] = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

        # debug
        self.partial_events: list[Sequence[tuple[bool, MapCondition]]] = list()

        self.conditions = plugin.load_plugins(
            paths.CONDITIONS_PATH,
            "conditions",
            interface=EventCondition,
        )

        # Mypy fails to typecheck here because
        # https://github.com/python/mypy/issues/4717
        # The workarounds are ugly, so we will wait
        # for that to be fixed.
        self.actions = plugin.load_plugins(
            paths.ACTIONS_PATH,
            "actions",
            interface=EventAction,  # type: ignore[type-abstract]
        )

    def reset(self) -> None:
        """Clear out running events.  Use when changing maps."""
        self.running_events = dict()
        self.current_map = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

    def get_action(
        self,
        name: str,
        parameters: Optional[Sequence[Any]] = None,
    ) -> Optional[EventAction]:
        """
        Get an action that is loaded into the engine.

        A new instance will be returned each time.

        Return ``None`` if action is not loaded.

        Parameters:
            name: Name of the action.
            parameters: List of parameters that the action accepts.

        Returns:
            New instance of the action with the appropriate parameters if
            that action is loaded. ``None`` otherwise.

        """
        parameters = parameters or []

        try:
            action = self.actions[name]

        except KeyError:
            error = f'Error: EventAction "{name}" not implemented'
            logger.warning(error)
            return None

        if parameters == [""]:
            return action()

        try:
            return action(*parameters)
        except TypeError as e:
            logger.warning(
                f"Error instantiating {action} with parameters {parameters}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error instantiating {action} with parameters {parameters}: {e}"
            )
            return None

    def get_actions(self) -> list[type[EventAction]]:
        """
        Return list of EventActions.

        """
        return list(self.actions.values())

    def get_condition(self, name: str) -> Optional[EventCondition]:
        """
        Get a condition that is loaded into the engine.

        A new instance will be returned each time.

        Return ``None`` if condition is not loaded.

        Parameters:
            name: Name of the condition.

        Returns:
            New instance of the condition if that condition is loaded.
            ``None`` otherwise.

        """
        # TODO: make generic
        try:
            return self.conditions[name]()
        except KeyError:
            logger.warning(f'EventCondition "{name}" not implemented')
            return None

    def get_conditions(self) -> list[type[EventCondition]]:
        """
        Return list of EventConditions.

        """
        return list(self.conditions.values())

    def check_condition(
        self,
        cond_data: MapCondition,
    ) -> bool:
        """
        Check if condition is true of false.

        Returns ``False`` if the condition is not loaded properly.

        Parameters:
            cond_data: The condition to check.

        Returns:
            The value of the condition.

        """
        map_condition = self.get_condition(cond_data.type)
        if map_condition is None:
            logger.debug(f'map condition "{cond_data.type}" is not loaded')
            return False

        result = map_condition.test(self.session, cond_data) == (
            cond_data.operator == "is"
        )
        logger.debug(
            f'map condition "{map_condition.name}": {result} ({cond_data})'
        )
        return result

    def execute_action(
        self,
        action_name: str,
        parameters: Optional[Sequence[Any]] = None,
        skip: bool = False,
    ) -> None:
        """
        Load and execute an action.

        This will cause the game to hang if an action waits on game changes.

        Parameters:
            action_name: Name of the action.
            parameters: Parameters of the action.
            skip: Boolean for skipping the action.update().

        """
        parameters = parameters or []

        action = self.get_action(action_name, parameters)
        if action is None:
            error_msg = f'Map action "{action_name}" is not loaded'
            logger.warning(error_msg)
            raise ValueError(error_msg)

        action._skip = skip

        if action.cancelled:
            logger.debug(f"Action '{action_name}' is cancelled, not executing")
            return

        try:
            return action.execute()
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {e}")
            raise

    def start_event(self, map_event: EventObject) -> None:
        """
        Begins execution of action list. Conditions are not checked.

        The event ID is used to prevent multiple copies of the same event from being started.

        Parameters:
            map_event: Event whose actions will be executed.

        """
        if map_event.id is None:
            raise ValueError("Event ID is required")

        if map_event.id not in self.running_events:
            logger.debug(f"Starting map event: {map_event.id}")
            logger.debug("Executing action list")
            logger.debug(map_event)

            token = RunningEvent(map_event)
            self.running_events[map_event.id] = token

            if map_event in self.session.client.inits:
                self.session.client.inits.remove(map_event)

    def process_map_event(self, map_event: EventObject) -> None:
        """
        Check the conditions of an event, and execute actions they are met.

        Actions will be started, but may finish much later.

        Parameters:
            map_event: Event to process.

        """
        if prepare.CONFIG.collision_map:
            # TODO: wrap with add_error_context
            # Debug mode: check all conditions and store results (slower)
            conds = [
                (self.check_condition(cond), cond) for cond in map_event.conds
            ]
            self.partial_events.append(conds)
            if all(result for result, _ in conds):
                self.start_event(map_event)
        else:
            # Optimal mode: start event if all conditions are met
            if all(self.check_condition(cond) for cond in map_event.conds):
                self.start_event(map_event)

    def process_map_events(self, events: Iterable[EventObject]) -> None:
        """
        Process all events in an iterable.

        Simple now, may become more complex.

        Parameters:
            events: Iterable of events to process.

        """
        for event in events:
            self.process_map_event(event)

    def update(self, dt: float) -> None:
        """
        Check all the MapEvents and start their actions if conditions are met.

        Parameters:
            dt: Amount of time passed in seconds since last frame.

        """
        # debug
        self.partial_events = list()
        self.check_conditions()
        self.update_running_events(dt)

    def check_conditions(self) -> None:
        """
        Checks conditions. If any are satisfied, start the MapActions.

        Actions may be started during this function.

        """
        # do the "init" events.  this will be done just once
        # TODO: make event engine generic, so can be used in global scope,
        # not just maps
        if self.session.client.inits:
            self.process_map_events(self.session.client.inits)

        # process any other events
        self.process_map_events(self.session.client.events)

    def cancel_event(self, event_id: int) -> None:
        """Cancels the event with the given ID."""
        if event_id in self.running_events:
            self.running_events[event_id].cancel()

    def cancel_all_events(self) -> None:
        """Cancels all currently running events."""
        for event in self.running_events.values():
            event.cancel()

    def update_running_events(self, dt: float) -> None:
        """
        Update the events that are running.

        Parameters:
            dt: Amount of time passed in seconds since last frame.

        """
        to_remove = set()
        current_map = self.current_map

        # Loop through the list of actions and update them
        for i, e in self.running_events.items():
            # If the current map has changed, then `reset` has also been
            # called, which replaced self.running_events with an empty dict.
            # We need to stop processing the running_events, as they may not
            # make sense on the new map. We need to explicitly guard for this
            # because actions within this loop can change the map.
            if current_map != self.current_map:
                # The map has just changed, so running_events should have been
                # emptied.
                assert not self.running_events
                return

            # Check for cancellation
            if e.cancelled:
                to_remove.add(i)
                continue

            while True:
                """
                * if RunningEvent is currently running an action, then continue
                    to do so
                * if not, attempt to get the next queued action
                * if no queued action, do not check the RunningEvent next frame
                * if there is an action, then update it
                * if action is finished, then clear the pointer to the action
                    and inc. the index, cleanup
                * RunningEvent will be checked next frame

                This loop will execute as many actions as possible for every
                MapEvent. For example, some actions like set_variable do not
                require several frames, so all of them will be processed this
                frame.

                If an action is not finished, then this loop breaks and will
                check another RunningEvent, but the position in the action list
                is remembered and will be restored.
                """
                if e.current_action is None:
                    next_action = e.get_next_action()

                    if next_action is None:
                        # no next action, so remove the running event
                        to_remove.add(i)
                        break

                    else:
                        # got an action, so start it
                        action = self.get_action(
                            next_action.type,
                            next_action.parameters,
                        )

                        if action is None:
                            # action was not loaded, so, break?  raise
                            # exception, idk
                            # TODO: raise custom exception instead of None
                            # return?
                            # TODO: decide what to do for actions not loaded
                            logger.debug("action is not loaded!")
                            to_remove.add(i)
                            break

                        else:
                            # start the action
                            # with add_error_context(e.map_event, next_action,
                            # self.session):
                            action.start()

                            # save the action that is running
                            e.current_action = action

                # update the action
                action = e.current_action
                if action.cancelled:
                    logger.debug(f"Action is cancelled, not updating")
                    e.advance()
                    e.current_action = None
                    continue
                # with add_error_context(e.map_event, e.current_map_action,
                # self.session):
                action.update()

                if action.done:
                    # action finished, so continue and do the next one,
                    # if available
                    action.cleanup()
                    e.advance()
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


@contextmanager
def add_error_context(
    event: EventObject,
    item: Union[MapCondition, MapAction],
    session: Session,
) -> Generator[None, None, None]:
    """
    Add error information about the involved condition or action.

    This should be used as a context manager for code that may
    fail associated with a particular condition or action.

    Parameters:
        event: Event associated with the condition or action.
        item: Condition or action that produces the error.
        session: Object containing the session information.

    """
    try:
        yield
    except Exception:
        from lxml import etree

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
                    event=etree.tostring(event_node)
                    .decode()
                    .split("\n")[0]
                    .strip(),
                    line_number=event_node.sourceline,
                )
            else:
                # This is either a condition or an action
                child_node = event_node.find(
                    ".//property[@name='%s']" % (item.name)
                )
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
