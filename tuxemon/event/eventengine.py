# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from tuxemon.event.eventbehavior import expand_behavior
from tuxemon.event.running import EventState, RunningCondition, RunningEvent
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.db import EventObject, ParameterizableRule, SpatialCondition
    from tuxemon.event.eventaction import ActionManager
    from tuxemon.event.eventbehavior import BehaviorManager
    from tuxemon.event.running import ConditionEvaluator
    from tuxemon.map.tuxemon import AbstractMap
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
        behavior_manager: BehaviorManager,
    ) -> None:
        self.session = session
        self.action_manager = action
        self.evaluator = evaluator
        self.behavior_manager = behavior_manager

        self.running_events: dict[int, RunningEvent] = dict()
        self.name = "Event"
        self.current_map: AbstractMap | None = None
        self._suspended: bool = False

        self.global_events: list[EventObject] = []
        self.triggered_global_events: set[int] = set()
        self._behavior_cache: dict[
            int, tuple[list[SpatialCondition], list[ParameterizableRule]]
        ] = {}

        # debug
        self.partial_events: list[Sequence[tuple[bool, SpatialCondition]]] = (
            list()
        )

    def set_current_map(self, new_map: AbstractMap | None) -> None:
        """Updates the current map."""
        if self.current_map != new_map:
            self.current_map = new_map

    def reset(self, new_map: AbstractMap | None = None) -> None:
        """Clear out running events.  Use when changing maps."""
        self.running_events = {}
        self.triggered_global_events = set()
        self._behavior_cache = {}
        self.set_current_map(new_map)

    def suspend(self) -> None:
        """
        Globally stops the EventEngine from checking conditions or processing running events.
        """
        if not self._suspended:
            logger.info("EventEngine suspended.")
            self._suspended = True

    def resume(self) -> None:
        """
        Resumes the EventEngine, allowing condition checking and event processing to continue.
        """
        if self._suspended:
            logger.info("EventEngine resumed.")
            self._suspended = False

    def execute_action(
        self,
        action_name: str,
        parameters: Sequence[Any] | None = None,
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
        if map_event.id in self.running_events:
            return

        _, behav_acts = self._get_behavior_expansion(map_event)
        combined_actions = behav_acts + list(map_event.acts)
        logger.debug(f"Starting map event: {map_event.id}")

        token = RunningEvent(map_event, combined_actions)
        token.running()
        self.running_events[map_event.id] = token

        if map_event in self.session.client.map_manager.inits:
            self.session.client.map_manager.remove_init(map_event)

    def process_map_event(self, map_event: EventObject) -> None:
        """
        Evaluates the conditions of a single map event and starts it if all
        conditions are met.

        This method wraps each condition in a RunningCondition, checks them
        using the evaluator, and determines whether the event should be
        triggered. If debug mode is enabled via `self.config.collision_map`,
        the condition results are stored in `self.partial_events` for inspection
        or debugging.

        Parameters:
            map_event: The event to evaluate and potentially start.
        """
        self._evaluate_and_queue_event(map_event)

    def update(self, dt: float) -> None:
        """
        Check all the MapEvents and start their actions if conditions are met.
        """
        if self._suspended:
            return

        self._behavior_cache = {}
        self.partial_events = []
        self.check_global_conditions()
        self.check_conditions()
        self.update_running_events(dt)

    def check_conditions(self) -> None:
        """
        Checks conditions. If any are satisfied, start the MapActions.

        Actions may be started during this function.
        """
        inits = list(self.session.client.map_manager.inits)
        events = list(self.session.client.map_manager.events)

        for event in inits:
            self.process_map_event(event)

        for event in events:
            self.process_map_event(event)

    def register_global_event(self, event: EventObject) -> bool:
        if any(e.id == event.id for e in self.global_events):
            logger.warning(f"Global event {event.id} is already registered.")
            return False

        self.global_events.append(event)
        self.global_events.sort(key=lambda e: e.priority, reverse=True)

        logger.debug(f"Global event {event.id} registered.")
        return True

    def unregister_global_event(self, event_id: int) -> bool:
        before_count = len(self.global_events)
        self.global_events = [
            event for event in self.global_events if event.id != event_id
        ]
        after_count = len(self.global_events)

        was_removed = before_count != after_count
        if was_removed:
            logger.debug(f"Global event {event_id} deregistered.")
        else:
            logger.warning(
                f"Global event {event_id} not found during deregistration."
            )

        self.triggered_global_events.discard(event_id)
        return was_removed

    def check_global_conditions(self) -> None:
        for event in self.global_events:
            if event.id in self.triggered_global_events:
                continue
            self._evaluate_and_queue_event(event, is_global=True)

    def _evaluate_and_queue_event(
        self, event: EventObject, is_global: bool = False
    ) -> None:
        behav_conds, _ = self._get_behavior_expansion(event)
        all_conditions = list(event.conds) + behav_conds

        if not all_conditions:
            return

        running_conditions = [
            RunningCondition(cond, self.evaluator) for cond in all_conditions
        ]
        all_met = all(rc.check() for rc in running_conditions)

        if CONFIG.collision_map:
            self.partial_events.append(
                [
                    (rc.result or False, rc.map_condition)
                    for rc in running_conditions
                ]
            )

        if all_met and event.id not in self.running_events:
            self.start_event(event)
            if is_global:
                self.triggered_global_events.add(event.id)

    def cancel_event(self, event_id: int) -> None:
        """Cancels the event with the given ID."""
        if event_id in self.running_events:
            self.running_events[event_id].cancel()
            self.triggered_global_events.discard(event_id)

    def cancel_all_events(self) -> None:
        """Cancels all currently running events."""
        for event in self.running_events.values():
            event.cancel()
        self.triggered_global_events.clear()

    def update_running_events(self, dt: float) -> None:
        """
        Update the events that are running.

        Parameters:
            dt: Amount of time passed in seconds since last frame.
        """
        current_map = self.current_map

        for event_id, running_event in list(self.running_events.items()):
            if not running_event.is_running():
                continue

            still_active = running_event.step(
                self.session, self.action_manager, dt
            )

            # Critical: Stop if the action triggered a map change
            if current_map != self.current_map:
                return

            if not still_active or running_event.state in (
                EventState.COMPLETED,
                EventState.CANCELLED,
            ):
                self.running_events.pop(event_id, None)

    def _get_behavior_expansion(
        self, event: EventObject
    ) -> tuple[list[SpatialCondition], list[ParameterizableRule]]:
        """
        Returns cached behavior expansion for an event within the current update cycle.
        Prevents expand() from being called twice (once for conditions, once for actions).
        """
        if event.id not in self._behavior_cache:
            self._behavior_cache[event.id] = expand_behavior(
                event, self.behavior_manager
            )
        return self._behavior_cache[event.id]
