# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from tuxemon.state.manager import StateManager

logger = logging.getLogger(__name__)


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
        self._state_queue: list[tuple[str, Mapping[str, Any]]] = []

    def queue_state(self, state_name: str, **kwargs: Any) -> None:
        """
        Queue a state to be pushed after the current state is popped or replaced.

        Use this to chain execution of states, without causing a
        state to get instanced before it is on top of the stack.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the __init__ method of the new state.
        """
        logger.debug(f"Queueing state: {state_name}")
        self._state_queue.append((state_name, kwargs))

    def handle_next_queued_state(self) -> bool:
        """
        Processes and activates the next state in the queue, if one exists.

        Returns:
            True if a state was processed and activated, False otherwise.
        """
        if self._state_queue:
            state_name, kwargs = self._state_queue.pop(0)
            logger.debug(
                f"Handling queued state: {state_name} (replacing current)"
            )
            self._state_manager_ref.replace_state(state_name, **kwargs)
            return True
        return False

    def get_queued_state_by_name(
        self,
        state_name: str,
    ) -> tuple[str, Mapping[str, Any]]:
        """
        Query the queued state stack for a state by the name supplied.

        Parameters:
            state_name: Name of a state.

        Returns:
            State with that name, if one exist.

        Raises:
            ValueError: If the state with the given name is not found in the queue.
        """
        for queued_state in self._state_queue:
            if queued_state[0] == state_name:
                return queued_state
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
        for i, (name, _) in enumerate(self._state_queue):
            if name == state_name:
                logger.debug(f"Removing queued state: {state_name}")
                del self._state_queue[i]
                return
        raise ValueError(f"State '{state_name}' not found in queue")

    def replace_queued_state(self, state_name: str, **new_kwargs: Any) -> None:
        """
        Removes a queued state by name.

        Parameters:
            state_name: Name of the state to remove.

        Raises:
            ValueError: If the state is not found in the queue.
        """
        for i, (name, _) in enumerate(self._state_queue):
            if name == state_name:
                logger.debug(f"Replacing queued state: {state_name}")
                self._state_queue[i] = (state_name, new_kwargs)
                return
        raise ValueError(f"State '{state_name}' not found in queue")

    def peek_next(self) -> Optional[tuple[str, Mapping[str, Any]]]:
        """
        Returns the next queued state without removing it.

        Returns:
            The next queued state, or None if the queue is empty.
        """
        return self._state_queue[0] if self._state_queue else None

    @property
    def has_queued_states(self) -> bool:
        """Returns True if there are states currently in the queue."""
        return bool(self._state_queue)

    @property
    def queued_states(self) -> Sequence[tuple[str, Mapping[str, Any]]]:
        """
        Sequence of states that are queued (read-only view).

        Returns:
            List of queued states.
        """
        return self._state_queue[:]
