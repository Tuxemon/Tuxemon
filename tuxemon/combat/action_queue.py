# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from tuxemon.combat.sort_manager import SortManager
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item


@dataclass
class EnqueuedAction:
    user: Union[Monster, NPC, None]
    method: Union[Technique, Item, Status, None]
    target: Monster

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

    def get_last_action(self) -> Optional[EnqueuedAction]:
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

    def enqueue(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the queue and history."""
        self._action_queue.append(action)
        self._action_history.add_action(turn, action)

    def add_pending(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the pending queue."""
        self._pending_queue.append((turn, action))

    def autoclean_pending(self) -> None:
        """Removes actions from the pending queue under certain conditions."""
        self._pending_queue = [
            (turn, pend)
            for turn, pend in self._pending_queue
            if not (
                (
                    pend.user
                    and isinstance(pend.user, Monster)
                    and pend.user.is_fainted
                )
                or pend.target.is_fainted
            )
        ]

    def from_pending_to_action(self, turn: int) -> None:
        """
        Removes actions from the pending queue and implements them in the
        action queue.
        """
        for _turn, pend in self._pending_queue[:]:
            if _turn == turn:
                self.enqueue(pend, turn)
                self._pending_queue.remove((turn, pend))

    def dequeue(self, action: EnqueuedAction) -> None:
        """Removes an action from the queue if it exists."""
        try:
            self._action_queue.remove(action)
        except ValueError:
            raise ValueError(f"Action {action} not found in queue")

    def pop(self) -> EnqueuedAction:
        """Removes and returns the last action from the queue."""
        return self._action_queue.pop()

    def is_empty(self) -> bool:
        """Returns True if the queue is empty, False otherwise."""
        return len(self._action_queue) == 0

    def clear_queue(self) -> None:
        """Clears the entire queue."""
        self._action_queue.clear()

    def clear_history(self) -> None:
        """Clears the entire history."""
        self._action_history.clear()

    def clear_pending(self) -> None:
        """Clears the entire pending queue."""
        self._pending_queue.clear()

    def sort(self) -> None:
        """
        Sorts the queue based on the action's sort key (game rules).
        * Techniques that damage are sorted by monster speed (fastest monsters first)
        * Items are sorted by trainer speed (fastest trainers first)
        * Actions are ordered from lowest to highest priority, with the highest priority
        actions last in the queue.
        """
        self._action_queue.sort(
            key=SortManager.get_action_sort_key, reverse=True
        )

    def swap(self, old: Monster, new: Monster) -> None:
        """Swaps the target of all actions in the queue from old to new."""
        for index, action in enumerate(self._action_queue):
            if action.target == old:
                self.__replace(index, action.user, action.method, new)

    def rewrite(
        self, monster: Monster, method: Union[Technique, Item, Status]
    ) -> None:
        """Rewrites the method of all actions in the queue for the given monster."""
        for index, action in enumerate(self._action_queue):
            if action.user == monster:
                self.__replace(index, monster, method, action.target)

    def __replace(
        self,
        index: int,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Status, None],
        target: Monster,
    ) -> None:
        """Replaces an action in the queue at the given index."""
        new_action = EnqueuedAction(user, method, target)
        self._action_queue[index] = new_action

    def get_last_action(
        self, turn: int, monster: Monster, field: str
    ) -> Optional[EnqueuedAction]:
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
