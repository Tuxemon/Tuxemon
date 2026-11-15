# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from heapq import heapify, heappush
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuxemon.state.manager import StateManager

logger = logging.getLogger(__name__)


@dataclass(order=True)
class QueuedState:
    priority: int
    name: str
    kwargs: Mapping[str, Any]
    activation_time: float | None = None
    expires_at: float | None = None
    source: str | None = None
    condition: Callable[[], bool] | None = None


class StateQueue:
    """
    Manages a queue of pending game states, allowing for deferred state transitions.
    """

    def __init__(self, state_manager_ref: StateManager) -> None:
        """
        Initializes the StateQueue.

        Parameters:
            state_manager_ref: A reference to the StateManager instance
                               that will activate the queued states.
        """
        self._state_manager_ref = state_manager_ref
        self._state_queue: list[QueuedState] = []

    def queue_state(
        self,
        state_name: str,
        priority: int = 10,
        activation_time: float | None = None,
        expires_at: float | None = None,
        source: str | None = None,
        condition: Callable[[], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Queue a state to be pushed after the current state is popped or replaced.

        Parameters:
            state_name: Name of the state to start.
            priority: Determines the order in which states are handled.
            activation_time: Optional Unix timestamp when the state becomes eligible.
            expires_at: Optional Unix timestamp after which the state is skipped.
            source: Optional metadata tag for tracking origin.
            condition: Optional callable that returns True if the state should be activated.
            kwargs: Arguments to pass to the __init__ method of the new state.
        """
        item = QueuedState(
            priority=priority,
            name=state_name,
            kwargs=kwargs,
            activation_time=activation_time,
            expires_at=expires_at,
            source=source,
            condition=condition,
        )
        heappush(self._state_queue, item)
        logger.debug(
            f"Queued state '{state_name}' with priority {priority}, "
            f"activation_time={activation_time}, expires_at={expires_at}, "
            f"source={source}, condition={condition}"
        )

    def handle_next_queued_state(self) -> bool:
        """
        Processes and activates the next eligible state in the queue.

        Returns:
            True if a state was processed and activated, False otherwise.
        """
        now = time.time()

        for i, state in enumerate(self._state_queue):
            # Skip states not yet ready
            if state.activation_time and now < state.activation_time:
                continue

            # Skip expired states
            if state.expires_at and now > state.expires_at:
                logger.info(f"Skipping expired state: {state.name}")
                continue

            # Skip states with unmet condition
            if state.condition and not state.condition():
                logger.info(
                    f"Skipping state '{state.name}' due to unmet condition"
                )
                continue

            # Activate and remove from queue
            state_to_activate = self._state_queue.pop(i)
            heapify(self._state_queue)
            logger.debug(f"Activating state: {state_to_activate.name}")
            self._state_manager_ref.replace_state(
                state_to_activate.name, **state_to_activate.kwargs
            )
            return True

        return False

    def get_queued_state_by_name(self, state_name: str) -> QueuedState:
        """
        Query the queued state stack for a state by the name supplied.

        Parameters:
            state_name: Name of a state.

        Returns:
            State with that name, if one exist.

        Raises:
            ValueError: If the state with the given name is not found in the queue.
        """
        for item in self._state_queue:
            if item.name == state_name:
                return item
        raise ValueError(f"Missing queued state {state_name}")

    def clear(self) -> None:
        """Clears all queued states."""
        logger.debug("Clearing all queued states")
        self._state_queue.clear()

    def remove_state_by_name(self, state_name: str) -> None:
        """
        Removes a queued state by name.

        Parameters:
            state_name: Name of the state to remove.

        Raises:
            ValueError: If the state is not found in the queue.
        """
        new_queue = [
            item for item in self._state_queue if item.name != state_name
        ]
        if len(new_queue) == len(self._state_queue):
            raise ValueError(f"State '{state_name}' not found in queue")
        self._state_queue[:] = new_queue
        heapify(self._state_queue)
        logger.debug(f"Removed queued state: {state_name}")

    def remove_expired_states(self) -> None:
        """Removes states from the queue that have passed their expiration time."""
        now = time.time()
        self._state_queue = [
            state
            for state in self._state_queue
            if state.expires_at is None or now <= state.expires_at
        ]
        heapify(self._state_queue)
        logger.debug("Removed expired states from queue")

    def replace_queued_state(
        self,
        state_name: str,
        *,
        new_kwargs: Mapping[str, Any] | None = None,
        new_priority: int | None = None,
        new_activation_time: float | None = None,
        new_expires_at: float | None = None,
        new_source: str | None = None,
        new_condition: Callable[[], bool] | None = None,
    ) -> None:
        """
        Replaces the attributes of a queued state by name.

        Parameters:
            state_name: Name of the state to update.
            new_kwargs: New arguments to pass to the state.
            new_priority: Optional new priority.
            new_activation_time: Optional new activation time.
            new_expires_at: Optional new expiration time.
            new_source: Optional new source tag.
            new_condition: Optional new condition callable for activation.

        Raises:
            ValueError: If the state is not found in the queue.
        """
        found = False
        for i, item in enumerate(self._state_queue):
            if item.name == state_name:
                updated_state = QueuedState(
                    priority=(
                        new_priority
                        if new_priority is not None
                        else item.priority
                    ),
                    name=item.name,
                    kwargs=(
                        new_kwargs if new_kwargs is not None else item.kwargs
                    ),
                    activation_time=(
                        new_activation_time
                        if new_activation_time is not None
                        else item.activation_time
                    ),
                    expires_at=(
                        new_expires_at
                        if new_expires_at is not None
                        else item.expires_at
                    ),
                    source=(
                        new_source if new_source is not None else item.source
                    ),
                    condition=(
                        new_condition
                        if new_condition is not None
                        else item.condition
                    ),
                )
                self._state_queue[i] = updated_state
                found = True
                break
        if not found:
            raise ValueError(f"State '{state_name}' not found in queue")
        heapify(self._state_queue)
        logger.debug(f"Replaced queued state attributes for: {state_name}")

    def peek_next(self) -> QueuedState | None:
        """
        Returns the next queued state without removing it.

        Returns:
            The next queued state, or None if the queue is empty.
        """
        if not self._state_queue:
            return None
        return self._state_queue[0]

    @property
    def has_queued_states(self) -> bool:
        """Returns True if there are states currently in the queue."""
        return bool(self._state_queue)

    @property
    def queued_states(self) -> Sequence[QueuedState]:
        """
        Sequence of states that are queued (read-only view), including priority.

        Returns:
            List of queued states with priority.
        """
        return sorted(self._state_queue)
