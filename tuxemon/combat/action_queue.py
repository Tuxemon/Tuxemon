# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tuxemon.combat.sort_manager import SortManager
from tuxemon.entity.npc import NPC
from tuxemon.monster.monster import Monster
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item

logger = logging.getLogger(__name__)


@dataclass
class EnqueuedAction:
    user: Monster | NPC | None
    method: Technique | Item | Status | None
    target: Monster
    sub_priority: float = field(default_factory=random.random)

    def __repr__(self) -> str:
        return f"EnqueuedAction(user={self.user}, method={self.method}, target={self.target})"


class ActionHistory:
    def __init__(self) -> None:
        self.history: list[tuple[int, EnqueuedAction]] = []

    def add_action(self, turn: int, action: EnqueuedAction) -> None:
        self.history.append((turn, action))

    def get_actions_by_turn(self, turn: int) -> list[EnqueuedAction]:
        return [action for _turn, action in self.history if _turn == turn]

    def clear(self) -> None:
        """Clears the entire action history."""
        self.history.clear()

    def get_actions_by_turn_range(
        self, start_turn: int, end_turn: int
    ) -> list[EnqueuedAction]:
        """Retrieves all actions that occurred between the specified turn range."""
        return [
            action
            for _turn, action in self.history
            if start_turn <= _turn <= end_turn
        ]

    def count_actions(self) -> int:
        """Returns the total number of actions recorded in history."""
        return len(self.history)

    def get_last_action(self) -> EnqueuedAction | None:
        """Retrieves the last action recorded in history."""
        return self.history[-1][1] if self.history else None

    def __repr__(self) -> str:
        """Returns a string representation of the ActionHistory."""
        action_count = len(self.history)
        # Get the last 3 actions for the sample
        sample_actions = self.history[-3:]
        sample_repr = ", ".join(
            f"({turn}, {action})" for turn, action in sample_actions
        )
        return f"ActionHistory(count={action_count}, sample=[{sample_repr}])"


class ActionQueue:
    def __init__(self) -> None:
        self._action_queue: list[EnqueuedAction] = []
        self._pending_queue: list[tuple[int, EnqueuedAction]] = []
        self._action_history = ActionHistory()
        self.current_turn = 0

    @property
    def queue(self) -> list[EnqueuedAction]:
        """Returns the current action queue."""
        return self._action_queue

    @property
    def history(self) -> ActionHistory:
        """Returns the current action history."""
        return self._action_history

    @property
    def pending(self) -> list[tuple[int, EnqueuedAction]]:
        """Returns the pending actions."""
        return self._pending_queue

    def set_current_turn(self, turn: int) -> None:
        self.current_turn = turn

    def enqueue(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the queue and history."""
        self._action_queue.append(action)
        self._action_history.add_action(turn, action)

    def add_pending(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the pending queue."""
        self._pending_queue.append((turn, action))

    def autoclean_pending(self) -> None:
        """Remove pending actions that are outdated or involve fainted monsters."""
        current = self.current_turn
        cleaned = []

        for turn, action in self._pending_queue:
            user_fainted = (
                isinstance(action.user, Monster) and action.user.is_fainted
            )
            target_fainted = action.target and action.target.is_fainted

            if turn >= current and not (user_fainted or target_fainted):
                cleaned.append((turn, action))

        self._pending_queue = cleaned

    def from_pending_to_action(self, turn: int) -> None:
        """
        Removes actions from the pending queue and implements them in the
        action queue.
        """
        to_move = [pend for t, pend in self._pending_queue if t == turn]
        self._pending_queue = [
            (t, p) for t, p in self._pending_queue if t != turn
        ]

        for action in to_move:
            self.enqueue(action, turn)

    def dequeue(self, action: EnqueuedAction) -> None:
        """Removes an action from the queue if it exists."""
        try:
            self._action_queue.remove(action)
            self.remove_from_history(action)
        except ValueError:
            raise ValueError(f"Action {action} not found in queue")

    def pop(self) -> EnqueuedAction:
        """Removes and returns the last action from the queue."""
        action = self._action_queue.pop()
        self.remove_from_history(action)
        return action

    def is_empty(self) -> bool:
        """Returns True if the queue is empty, False otherwise."""
        return len(self._action_queue) == 0

    def clear_queue(self) -> None:
        """Clears the entire queue."""
        for _, action in list(self._action_history.history):
            if action in self._action_queue:
                self.remove_from_history(action)
        self._action_queue.clear()

    def clear_history(self) -> None:
        """Clears the entire history."""
        self._action_history.clear()

    def clear_pending(self) -> None:
        """Clears the entire pending queue."""
        self._pending_queue.clear()

    def sort(self) -> None:
        """Sort the action queue using cached sort keys for efficiency."""
        key_cache = {
            id(action): SortManager.get_action_sort_key(action)
            for action in self._action_queue
        }

        self._action_queue.sort(
            key=lambda a: (
                -key_cache[id(a)].primary_order,
                key_cache[id(a)].speed,
                key_cache[id(a)].tie_breaker,
            )
        )

        # Tie-breaker logging
        for a, b in zip(self._action_queue, self._action_queue[1:]):
            ka = key_cache[id(a)]
            kb = key_cache[id(b)]

            if (
                ka.primary_order == kb.primary_order
                and ka.speed == kb.speed
                and a.user
                and b.user
            ):
                logger.debug(
                    f"Speed Tie: {a.user.name} vs {b.user.name} resolved by tie-breaker."
                )

    def swap(self, old: Monster, new: Monster) -> None:
        """Redirect all actions targeting 'old' to target 'new'."""
        for action in self._action_queue:
            if action.target is old:
                action.target = new

    def rewrite(
        self, monster: Monster, method: Technique | Item | Status
    ) -> None:
        """Rewrite the method of all actions performed by the given monster."""
        for action in self._action_queue:
            if action.user is monster:
                action.method = method

    def remove_from_history(self, action: EnqueuedAction) -> None:
        """Remove the exact action instance from history."""
        self._action_history.history = [
            (t, a)
            for (t, a) in self._action_history.history
            if a is not action
        ]

    def get_last_action(
        self, turn: int, monster: Monster, field: str
    ) -> EnqueuedAction | None:
        """
        Retrieves the last action involving the specified monster in the given turn.

        Parameters:
            turn: The turn number to search in.
            monster: The monster to search for.
            field: The field to search in ('user' or 'target').

        Returns:
            The last matching action, or None if not found.
        """
        if field not in ("user", "target"):
            raise ValueError(f"{field} must be 'user' or 'target'")

        for _turn, action in reversed(self._action_history.history):
            if _turn == turn and (
                (field == "user" and action.user == monster)
                or (field == "target" and action.target == monster)
            ):
                return action

        return None

    def get_all_actions_by_turn(self, turn: int) -> list[EnqueuedAction]:
        """
        Retrieves all actions that occurred in the specified turn.

        Parameters:
            turn: The turn number to retrieve actions for.

        Returns:
            A list of actions that occurred in the specified turn.
        """
        return self._action_history.get_actions_by_turn(turn)

    def remove_monster_actions(self, monster: Monster) -> None:
        """Remove all actions involving the given monster from queue, pending, and history."""

        # Remove from main queue
        self._action_queue = [
            action
            for action in self._action_queue
            if action.user is not monster and action.target is not monster
        ]

        # Remove from pending queue
        self._pending_queue = [
            (t, action)
            for (t, action) in self._pending_queue
            if action.user is not monster and action.target is not monster
        ]

        # Remove from history
        self._action_history.history = [
            (t, action)
            for (t, action) in self._action_history.history
            if action.user is not monster and action.target is not monster
        ]

    def schedule_action_in_turns(
        self, action: EnqueuedAction, turns: int
    ) -> None:
        target_turn = self.current_turn + turns
        self.add_pending(action, target_turn)

    def has_pending_for(self, monster: Monster) -> bool:
        return any(action.user is monster for _, action in self._pending_queue)
