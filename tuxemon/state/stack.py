# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.state.state import State

logger = logging.getLogger(__name__)


class StateStack:
    """
    Manages the stack of active game states and tracks which states should resume.
    """

    def __init__(self) -> None:
        self._stack: deque[State] = deque()
        self._resume_set: set[State] = set()

    def push(self, state: State) -> None:
        """Push a new state onto the stack and mark it for resume."""
        self._resume_set.add(state)
        self._stack.appendleft(state)

    def pop(self, state: State | None = None) -> State:
        """Pop a state from the stack."""
        if not self._stack:
            raise RuntimeError("Attempted to pop from an empty state stack")

        state = state or self._stack[0]
        try:
            self._stack.remove(state)
        except ValueError:
            raise RuntimeError("State not found in stack")

        return state

    def replace(self, new_state: State) -> State:
        """Replace the current state with a new one."""
        if not self._stack:
            raise RuntimeError(
                "Attempted to replace state when stack is empty"
            )

        old_state = self._stack.popleft()
        self.push(new_state)
        return old_state

    def mark_for_resume(self, state: State) -> None:
        """Mark a state to be resumed later."""
        self._resume_set.add(state)

    def mark_resumed(self, state: State) -> None:
        """Remove a state from the resume set."""
        self._resume_set.discard(state)

    def should_resume(self, state: State) -> bool:
        """Check if a state is marked to resume."""
        return state in self._resume_set

    def remove(self, state: State) -> None:
        """Remove a specific state from the stack."""
        try:
            self._stack.remove(state)
            self._resume_set.discard(state)
        except ValueError:
            raise RuntimeError("Attempted to remove a state not in the stack")

    def current(self) -> State | None:
        """Return the current (top) state."""
        return self._stack[0] if self._stack else None

    def all(self) -> Sequence[State]:
        """Return all states in the stack."""
        return list(self._stack)

    def get_states_by_name(self, name: str) -> list[State]:
        """Find a state in the stack by its name."""
        matches = [state for state in self._stack if state.name == name]
        if not matches:
            raise ValueError(f"State with name '{name}' not found")
        return matches
