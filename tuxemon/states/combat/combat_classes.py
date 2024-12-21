# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import NamedTuple, Optional, Union

from tuxemon import prepare
from tuxemon.animation_entity import AnimationEntity
from tuxemon.condition.condition import Condition
from tuxemon.item.item import Item
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.sprite import Sprite
from tuxemon.technique.technique import Technique


class MethodAnimationCache:
    def __init__(self) -> None:
        self._sprites: dict[
            Union[Technique, Condition, Item], Optional[Sprite]
        ] = {}

    def get(
        self, method: Union[Technique, Condition, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return a sprite usable as a method (technique, item, condition) animation.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        try:
            return self._sprites[method]
        except KeyError:
            sprite = self.load_method_animation(method, is_flipped)
            self._sprites[method] = sprite
            return sprite

    @staticmethod
    def load_method_animation(
        method: Union[Technique, Condition, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return animated sprite from a technique, condition or item.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        if not method.animation:
            return None

        ani = AnimationEntity(method.animation)
        if is_flipped:
            ani.play.flip(method.flip_axes)
        return Sprite(animation=ani.play)


class EnqueuedAction(NamedTuple):
    user: Union[Monster, NPC, None]
    method: Union[Technique, Item, Condition, None]
    target: Monster


def get_action_sort_key(action: EnqueuedAction) -> tuple[int, int]:
    """
    Returns a tuple representing the sort key for the given action.

    The sort key is a tuple of two integers: the primary order and the secondary order.
    The primary order is determined by the action's sort type, and the secondary order
    is determined by the user's speed test result (if applicable).

    If the action's method is None, or if the action's user is None, the function returns
    a default sort key of (0, 0).
    """
    if action.method is None:
        return 0, 0
    else:
        action_sort_type = action.method.sort
        primary_order = prepare.SORT_ORDER.index(action_sort_type)

        if action_sort_type in ["meta", "potion"]:
            return primary_order, 0
        else:
            if action.user is None:
                return 0, 0
            else:
                return primary_order, -action.user.speed_test(action)


class ActionQueue:

    def __init__(self) -> None:
        self._action_queue: list[EnqueuedAction] = []
        self._action_history: list[tuple[int, EnqueuedAction]] = []

    @property
    def queue(self) -> list[EnqueuedAction]:
        """Returns the current action queue."""
        return self._action_queue

    @property
    def history(self) -> list[tuple[int, EnqueuedAction]]:
        """Returns the current action history."""
        return self._action_history

    def enqueue(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the queue and history."""
        self._action_queue.append(action)
        self._action_history.append((turn, action))

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

    def sort(self) -> None:
        """
        Sorts the queue based on the action's sort key (game rules).
        * Techniques that damage are sorted by monster speed (fastest monsters first)
        * Items are sorted by trainer speed (fastest trainers first)
        * Actions are ordered from lowest to highest priority, with the highest priority
        actions last in the queue.
        """
        self._action_queue.sort(key=get_action_sort_key, reverse=True)

    def swap(self, old: Monster, new: Monster) -> None:
        """Swaps the target of all actions in the queue from old to new."""
        for index, action in enumerate(self._action_queue):
            if action.target == old:
                self.__replace(index, action.user, action.method, new)

    def rewrite(
        self, monster: Monster, method: Union[Technique, Item, Condition]
    ) -> None:
        """Rewrites the method of all actions in the queue for the given monster."""
        for index, action in enumerate(self._action_queue):
            if action.user == monster:
                self.__replace(index, monster, method, action.target)

    def __replace(
        self,
        index: int,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Condition, None],
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

        for _turn, action in reversed(self._action_history):
            if _turn == turn and (
                field == "user"
                and action.user == monster
                or field == "target"
                and action.target == monster
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

        return [
            action for _turn, action in self._action_history if _turn == turn
        ]


class DamageReport(NamedTuple):
    attack: Monster
    defense: Monster
    damage: int
