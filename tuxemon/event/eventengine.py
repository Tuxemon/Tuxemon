# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Optional, Union

from tuxemon import prepare
from tuxemon.event.running import EventState, RunningCondition, RunningEvent

if TYPE_CHECKING:
    from tuxemon.event import EventObject, MapAction, MapCondition
    from tuxemon.event.eventaction import ActionManager
    from tuxemon.event.running import ConditionEvaluator
    from tuxemon.map.map_tuxemon import TuxemonMap
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        session: Session,
        action: ActionManager,
        evaluator: ConditionEvaluator,
    ) -> None:
        self.session = session
        self.action_manager = action
        self.evaluator = evaluator

        self.running_events: dict[int, RunningEvent] = dict()
        self.name = "Event"
        self.current_map: Optional[TuxemonMap] = None
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

        self.global_events: list[EventObject] = []
        self.triggered_global_events: set[int] = set()

        # debug
        self.partial_events: list[Sequence[tuple[bool, MapCondition]]] = list()

    def set_current_map(self, new_map: Optional[TuxemonMap]) -> None:
        """Updates the current map."""
        if self.current_map != new_map:
            self.current_map = new_map

    def reset(self) -> None:
        """Clear out running events.  Use when changing maps."""
        self.running_events = dict()
        self.set_current_map(None)
        self.timer = 0.0
        self.wait = 0.0
        self.button = None

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

        action = self.action_manager.get_action(action_name, parameters)
        if action is None:
            error_msg = f'Map action "{action_name}" is not loaded'
            logger.warning(error_msg)
            raise ValueError(error_msg)

        action._skip = skip

        if action.cancelled:
            logger.debug(f"Action '{action_name}' is cancelled, not executing")
            return

        try:
            return action.execute(self.session)
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
            token.running()
            self.running_events[map_event.id] = token

            if map_event in self.session.client.map_manager.inits:
                self.session.client.map_manager.inits.remove(map_event)

    def process_map_event(self, map_event: EventObject) -> None:
        """
        Evaluates the conditions of a single map event and starts it if all
        conditions are met.

        This method wraps each condition in a RunningCondition, checks them
        using the evaluator, and determines whether the event should be
        triggered. If debug mode is enabled via `prepare.CONFIG.collision_map`,
        the condition results are stored in `self.partial_events` for inspection
        or debugging.

        Parameters:
            map_event: The event to evaluate and potentially start.
        """
        running_conditions = [
            RunningCondition(cond, self.evaluator) for cond in map_event.conds
        ]
        all_met = all(rc.check() for rc in running_conditions)

        if prepare.CONFIG.collision_map:
            self.partial_events.append(
                [
                    (rc.result or False, rc.map_condition)
                    for rc in running_conditions
                ]
            )

        if all_met:
            self.start_event(map_event)

    def update(self, dt: float) -> None:
        """
        Check all the MapEvents and start their actions if conditions are met.

        Parameters:
            dt: Amount of time passed in seconds since last frame.
        """
        # debug
        self.partial_events = []
        self.check_global_conditions()
        self.check_conditions()
        self.update_running_events(dt)

    def check_conditions(self) -> None:
        """
        Checks conditions. If any are satisfied, start the MapActions.

        Actions may be started during this function.
        """
        for event in list(self.session.client.map_manager.inits):
            self.process_map_event(event)

        # Then process regular map events
        for event in list(self.session.client.map_manager.events):
            self.process_map_event(event)

    def register_global_event(self, event: EventObject) -> None:
        if event.id is None:
            raise ValueError("Global event must have an ID")
        self.global_events.append(event)

    def check_global_conditions(self) -> None:
        for event in self.global_events:
            if event.id in self.triggered_global_events:
                continue

            running_conditions = [
                RunningCondition(cond, self.evaluator) for cond in event.conds
            ]
            all_met = all(rc.check() for rc in running_conditions)

            if prepare.CONFIG.collision_map:
                self.partial_events.append(
                    [
                        (rc.result or False, rc.map_condition)
                        for rc in running_conditions
                    ]
                )

            if all_met:
                self.start_event(event)
                if event.id is None:
                    raise ValueError("Global event must have an ID")
                self.triggered_global_events.add(event.id)

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
        current_map = self.current_map

        running_events_to_process = [
            (event_id, event)
            for event_id, event in self.running_events.items()
            if event.is_running()
        ]

        for event_id, running_event in running_events_to_process:
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

            if not self.process_running_event(running_event):
                # Event is complete or failed; mark it as completed
                running_event.complete()

        # Clean up completed or cancelled events outside the loop
        to_remove = [
            event_id
            for event_id, event in self.running_events.items()
            if event.state in (EventState.COMPLETED, EventState.CANCELLED)
        ]

        for event_id in to_remove:
            self.running_events.pop(event_id, None)

    def process_running_event(self, running_event: RunningEvent) -> bool:
        """
        Processes a single running event by handling its current or next action.

        Parameters:
            running_event: The event being processed.

        Returns:
            True if the event continues to run, False if it is complete.
        """
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
            # Check if the event was cancelled during processing
            if running_event.is_cancelled():
                logger.debug("Running event was cancelled.")
                return False

            current_action = running_event.current_action

            # Handle initialization of the next action if none is active
            if current_action is None:
                if not self.handle_next_action(running_event):
                    return False  # Event is complete
                continue

            # Check for cancellation
            if current_action.cancelled:
                logger.debug("Action is cancelled, advancing to the next one.")
                running_event.advance()
                running_event.current_action = None
                continue

            # with add_error_context(e.map_event, e.current_map_action,
            # self.session):
            current_action.update(self.session)

            if current_action.done:
                # action finished, so continue and do the next one,
                # if available
                current_action.cleanup(self.session)
                running_event.advance()
                running_event.current_action = None
                logger.debug(f"Action finished: {current_action}")
            else:
                # Action is still running, exit the loop
                return True

    def handle_next_action(self, running_event: RunningEvent) -> bool:
        """
        Initializes the next action for a running event.

        Parameters:
            running_event: The event being processed.

        Returns:
            True if a new action was successfully started, False if none exist.
        """
        next_action_data = running_event.get_next_action()

        if next_action_data is None:
            # No more actions; event is complete
            running_event.complete()
            return False

        action = self.action_manager.get_action(
            next_action_data.type, next_action_data.parameters
        )
        if action is None:
            logger.debug("Action is not loaded, skipping event.")
            return False

        # start the action
        # with add_error_context(e.map_event, next_action, self.session):
        action.start(self.session)
        running_event.current_action = action
        return True


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
    except Exception as original_exc:
        from lxml import etree

        file_name = session.client.map_manager.get_map_filepath()
        try:
            tree = etree.parse(file_name)
            event_node = tree.find(f"//object[@id='{event.id}']")
        except Exception as parse_exc:
            logger.error(
                f"Failed to parse map file '{file_name}': {parse_exc}"
            )
            raise original_exc

        msg_lines = [f"\nError in map file: {file_name}"]

        if event_node is not None:
            event_summary = (
                etree.tostring(event_node).decode().split("\n")[0].strip()
            )
            msg_lines.append(f"Event: {event_summary}")
            msg_lines.append(f"Line: {event_node.sourceline}")

            if item.name:
                child_node = event_node.find(
                    f".//property[@name='{item.name}']"
                )
                if child_node is not None:
                    child_summary = etree.tostring(child_node).decode().strip()
                    msg_lines.append(f"Property: {child_summary}")
                    msg_lines.append(f"Line: {child_node.sourceline}")
        else:
            msg_lines.append(f"Event with ID '{event.id}' not found in XML.")

        print(dedent("\n".join(msg_lines)))
        raise original_exc
