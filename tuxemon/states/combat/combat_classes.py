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


class ActionQueue:
    _action_queue: list[EnqueuedAction] = []

    @property
    def queue(self) -> list[EnqueuedAction]:
        """Returns the current action queue."""
        return self._action_queue

    def enqueue(self, action: EnqueuedAction) -> None:
        """Adds an action to the end of the queue."""
        self._action_queue.append(action)

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

    def sort(self) -> None:
        """Sorts the queue based on the action's sort key (game rules).
        * Techniques that damage are sorted by monster speed
        * Items are sorted by trainer speed
        """

        def get_action_sort_key(action: EnqueuedAction) -> tuple[int, int]:
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
                        return primary_order, action.user.speed_test(action)

        self._action_queue.sort(key=get_action_sort_key, reverse=True)

        # Custom sorting to handle same primary order
        for i in range(len(self._action_queue) - 1):
            if self._action_queue[i][0] == self._action_queue[i + 1][0]:
                self._action_queue[i : i + 2] = sorted(
                    self._action_queue[i : i + 2], key=lambda x: (x[0], -x[1])
                )

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


class DamageReport(NamedTuple):
    attack: Monster
    defense: Monster
    damage: int
