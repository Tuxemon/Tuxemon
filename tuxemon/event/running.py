# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuxemon.db import EventObject, ParameterizableRule, SpatialCondition
    from tuxemon.event.eventaction import ActionManager, EventAction
    from tuxemon.event.eventcondition import ConditionManager
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


class EventState(Enum):
    WAITING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    CANCELLED = auto()


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
        "actions",
        "context",
        "action_index",
        "current_action",
        "state",
        "priority",
        "elapsed_time",
    )

    def __init__(
        self,
        map_event: EventObject,
        expanded_actions: list[ParameterizableRule],
    ) -> None:
        self.map_event = map_event
        self.actions = expanded_actions
        self.context: dict[str, Any] = {}
        self.action_index: int = 0
        self.current_action: EventAction | None = None
        self.state = EventState.WAITING
        self.priority = map_event.priority
        self.elapsed_time: float = 0.0

    def tick(self, dt: float) -> bool:
        self.elapsed_time += dt

        # Check for delay
        if (
            self.map_event.delay is not None
            and self.elapsed_time < self.map_event.delay
        ):
            return False

        # Watchdog: Timeout prevents infinite event hangs (opt-in)
        if (
            self.map_event.timeout is not None
            and self.elapsed_time > self.map_event.timeout
        ):
            logger.warning(
                f"Event {self.map_event.id} reached timeout of {self.map_event.timeout}s"
            )
            self.cancel()
            return False

        return True

    def step(
        self,
        session: Session,
        action_manager: ActionManager,
        dt: float,
    ) -> bool:
        """
        Advance this event by one frame.
        Returns True if the event is still active, False if finished or cancelled.
        """
        if self.state in (EventState.COMPLETED, EventState.CANCELLED):
            return False

        return self.process(session, action_manager, dt)

    def process(
        self, session: Session, action_manager: ActionManager, dt: float
    ) -> bool:
        """
        Processes the event's actions.

        Returns:
            True - event is still alive (delay, long-running action)
            False - event is finished or cancelled
        """
        # Delay / timeout
        if not self.tick(dt):
            return self.is_alive()

        max_actions_per_frame = len(self.actions) + 1
        actions_this_frame = 0

        while True:
            if self.is_cancelled():
                logger.debug("Running event was cancelled.")
                return False

            # If no action is active, try to load the next one
            if self.current_action is None:
                if actions_this_frame >= max_actions_per_frame:
                    logger.warning(
                        f"Event {self.map_event.id} exhausted action budget "
                        f"in a single frame — yielding."
                    )
                    return True

                next_data = self.get_next_action()
                if next_data is None:
                    self.complete()
                    return False

                action = action_manager.get_action(
                    next_data.type, next_data.parameters
                )
                if action is None:
                    logger.error(
                        f"Invalid action returned for '{next_data.type}'"
                    )
                    self.cancel()
                    return False

                action.on_start(session)
                self.current_action = action
                actions_this_frame += 1

                # Edge case: action cancelled itself during on_start()
                if self.current_action.cancelled:
                    self.advance()
                    self.current_action = None
                    continue

            # Advance if action was cancelled between frames
            if self.current_action.cancelled:
                self.advance()
                self.current_action = None
                continue

            # Update the current action
            self.current_action.update(session, dt)

            # Safety: action should not clear itself during update
            if self.current_action is None:
                logger.error(
                    "Action cleared itself unexpectedly during update"
                )
                self.cancel()
                return False

            # If action finished, clean up and move to next one in the same frame
            if self.current_action.done:
                self.current_action.cleanup(session)
                self.advance()
                self.current_action = None
                continue

            # Action is still running (multi-frame)
            return True

    def get_next_action(self) -> ParameterizableRule | None:
        """Return the next action, or None if the event is completed."""
        if self.action_index >= len(self.actions):
            return None

        return self.actions[self.action_index]

    def reset(self) -> None:
        self.action_index = 0
        self.current_action = None
        self.elapsed_time = 0.0
        self.state = EventState.WAITING
        self.context.clear()

    def advance(self) -> None:
        self.action_index += 1

    def cancel(self) -> None:
        self.state = EventState.CANCELLED

    def complete(self) -> None:
        self.state = EventState.COMPLETED

    def running(self) -> None:
        self.state = EventState.RUNNING

    def is_alive(self) -> bool:
        return self.state not in (EventState.COMPLETED, EventState.CANCELLED)

    def is_cancelled(self) -> bool:
        return self.state == EventState.CANCELLED

    def is_running(self) -> bool:
        return self.state == EventState.RUNNING

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<RunningEvent ID={self.map_event.id} "
            f"State={self.state.name} "
            f"Priority={self.priority} "
            f"ActionIndex={self.action_index}>"
        )


class ConditionState(Enum):
    MET = auto()
    FAILED = auto()
    CANCELLED = auto()


class RunningCondition:
    __slots__ = (
        "map_condition",
        "evaluator",
        "state",
        "result",
    )

    def __init__(
        self, map_condition: SpatialCondition, evaluator: ConditionEvaluator
    ) -> None:
        self.map_condition = map_condition
        self.evaluator = evaluator
        self.state = ConditionState.FAILED
        self.result: bool | None = None

    def cancel(self) -> None:
        self.state = ConditionState.CANCELLED

    def is_cancelled(self) -> bool:
        return self.state == ConditionState.CANCELLED

    def is_met(self) -> bool:
        return self.state == ConditionState.MET

    def is_failed(self) -> bool:
        return self.state == ConditionState.FAILED

    def check(self) -> bool:
        if self.is_cancelled():
            self.result = False
            return False

        try:
            passed = self.evaluator.evaluate(self.map_condition)
            self.result = passed
            self.state = (
                ConditionState.MET if passed else ConditionState.FAILED
            )
            return passed
        except Exception as e:
            logger.error(
                f"Error checking condition '{self.map_condition}': {e}"
            )
            self.state = ConditionState.FAILED
            self.result = False
            return False


class ConditionEvaluator:
    def __init__(self, session: Session, condition_manager: ConditionManager):
        self.session = session
        self.condition_manager = condition_manager

    def evaluate(self, map_condition: SpatialCondition) -> bool:
        condition = self.condition_manager.get_condition(map_condition)
        if condition is None:
            raise ValueError(
                f"Condition type '{map_condition.type}' not found."
            )

        try:
            self.session.current_condition_box = map_condition.box
            result = condition.test(self.session)
        finally:
            self.session.current_condition_box = None

        return result == condition.is_expected
