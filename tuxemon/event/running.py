# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from tuxemon.event import EventObject, MapAction, MapCondition
    from tuxemon.event.eventaction import EventAction
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
        "context",
        "action_index",
        "current_action",
        "current_map_action",
        "state",
    )

    def __init__(self, map_event: EventObject) -> None:
        self.map_event = map_event
        self.context: dict[str, Any] = dict()
        self.action_index = 0
        self.current_action: Optional[EventAction] = None
        self.current_map_action = None
        self.state = EventState.WAITING

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
        self.state = EventState.CANCELLED

    def complete(self) -> None:
        self.state = EventState.COMPLETED

    def running(self) -> None:
        self.state = EventState.RUNNING

    def is_cancelled(self) -> bool:
        return self.state == EventState.CANCELLED

    def is_running(self) -> bool:
        return self.state == EventState.RUNNING


class ConditionState(Enum):
    WAITING = auto()
    CHECKING = auto()
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
        self, map_condition: MapCondition, evaluator: ConditionEvaluator
    ) -> None:
        self.map_condition = map_condition
        self.evaluator = evaluator
        self.state = ConditionState.WAITING
        self.result: Optional[bool] = None

    def start_check(self) -> None:
        self.state = ConditionState.CHECKING

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

        self.start_check()
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

    def evaluate(self, map_condition: MapCondition) -> bool:
        condition = self.condition_manager.get_condition(map_condition)
        if condition is None:
            raise ValueError(
                f"Condition type '{map_condition.type}' not found."
            )

        result = condition.test(self.session, map_condition)
        return result == condition.is_expected
