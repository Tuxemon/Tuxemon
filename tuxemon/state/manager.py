# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, overload

from tuxemon.constants import paths
from tuxemon.state.factory import StateFactory
from tuxemon.state.loader import StateLoader
from tuxemon.state.queue import QueuedState, StateQueue
from tuxemon.state.stack import StateStack
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.state.repository import StateRepository

logger = logging.getLogger(__name__)

DEFAULT_BASE_STATE_COUNT: int = 2  # BackgroundState + WorldState

StateType = TypeVar("StateType", bound="State")


class StateManager:
    """
    Allows game states to be managed like a queue.

    Parameters:
        package: Name of package to search for states.
        event: Manages events for executing custom logic during state changes.
        repository: Repository for accessing state instances.
        on_state_change: Optional callback to be executed when top state
            changes.
    """

    def __init__(
        self,
        package: str,
        client: BaseClient,
        repository: StateRepository,
        on_state_change: Callable[..., None] | None = None,
        state_loader: StateLoader | None = None,
    ) -> None:
        self.package = package
        self.client = client
        self.event_bus = client.event_bus
        self.state_repository = repository
        self.state_loader = state_loader or StateLoader(package, paths.LIBDIR)
        self.state_stack = StateStack()
        self.state_factory = StateFactory(self.client, self.state_repository)
        self.state_queue = StateQueue(self)

        if on_state_change:
            self.register_global_event("on_state_change", on_state_change)
        else:
            self.register_global_event(
                "on_state_change", lambda *args, **kwargs: None
            )

        self.register_global_event("pre_state_update", lambda time_delta: None)
        self.register_global_event(
            "post_state_update", lambda time_delta: None
        )

    def register_global_event(
        self, event_name: str, callback: Callable[..., None], priority: int = 0
    ) -> None:
        self.event_bus.subscribe(event_name, callback, priority)

    def unregister_global_event(
        self, event_name: str, callback: Callable[..., None]
    ) -> None:
        self.event_bus.unsubscribe(event_name, callback)

    def trigger_global_event(
        self, event_name: str, *args: Any, **kwargs: Any
    ) -> None:
        self.event_bus.publish(event_name, *args, **kwargs)

    def has_listeners_for_event(self, event_name: str) -> bool:
        return self.event_bus.has_listeners_for_event(event_name)

    def register_state(self, state: type[State]) -> None:
        """Add a state class."""
        name = state.__name__
        logger.debug(f"loading state: {name}")
        self.state_repository.add_state(state)

    def is_in_base_map_state(self, base_count: int | None = None) -> bool:
        """Return True if the active state count matches the base map state count."""
        base_count = base_count or DEFAULT_BASE_STATE_COUNT
        return len(self.active_states) == base_count

    def has_extra_states(self, base_count: int | None = None) -> bool:
        """Return True if more than the base map states are active."""
        base_count = base_count or DEFAULT_BASE_STATE_COUNT
        return len(self.active_states) > base_count

    def update(self, dt: float) -> None:
        """
        Run update on all active states, which doing some internal housekeeping.

        WIP. This may change at some point, especially handling of paused
        states.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        logger.debug("updating states")
        self.trigger_global_event("pre_state_update", dt)
        for state in self.active_states:
            self._check_resume(state)
            state.update(dt)
        self.trigger_global_event("post_state_update", dt)

    def _check_resume(self, state: State) -> None:
        """
        Call resume on states that are in the resume set.

        Typically states will resume right before an update, but if an update
        has not been called before an update, then the resume will be missed.

        This is used to enforce the symmetry between resume/pause calls.

        Parameters:
            state: State to check for resume
        """
        if self.state_stack.should_resume(state):
            logger.debug(f"removing {state.name} from resume set")
            self.state_stack.mark_resumed(state)
            state.resume()

    def query_all_states(self) -> Mapping[str, type[State]]:
        """Return a dictionary of all loaded states."""
        return self.state_repository.all_states()

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
        Queue a state to be pushed after the top state is popped or replaced.
        """
        self.state_queue.queue_state(
            state_name,
            priority=priority,
            activation_time=activation_time,
            expires_at=expires_at,
            source=source,
            condition=condition,
            **kwargs,
        )

    def pop_current_state(self) -> None:
        """Pop the current state from the stack."""
        if not self.state_stack.all():
            raise RuntimeError("Attempted to pop state when stack was empty.")

        state = self.state_stack.pop()
        logger.debug(f"Pop state: {state.name}")

        self._check_resume(state)
        state.pause()
        state.shutdown()

        current = self.state_stack.current()
        if current is not None:
            self.state_stack.mark_for_resume(current)

        if self.has_listeners_for_event("on_state_change"):
            self.trigger_global_event("on_state_change")

    def handle_queued_state(self) -> None:
        """Handle a queued state if one exists."""
        self.state_queue.handle_next_queued_state()

    def pop_state(self, state: State | None = None) -> None:
        """
        Pop some state.

        The default state is the current one. The previously running state
        will resume unless there is a queued state, which becomes the new
        current state instead of the previous.

        Parameters:
            state: The state to remove from the stack. Use None (or omit) for
                the current state.
        """
        if self.state_queue.has_queued_states:
            self.handle_queued_state()
            return

        if not self.state_stack.all():
            logger.critical("Attempted to pop from an empty state stack")
            raise RuntimeError("State stack is empty")

        try:
            state = (
                state or self.state_stack.current()
            )  # Default to current state

            if state is None:
                raise RuntimeError("No state to pop")

            if state == self.state_stack.current():
                self.pop_current_state()
            else:
                logger.debug(
                    f"Pop-remove state: {state.name} (from middle of stack)"
                )
                self.state_stack.remove(state)
                state.shutdown()

        except ValueError:
            logger.critical("Attempted to remove a state not in the stack")
            raise RuntimeError

    def remove_state_by_name(self, state_name: str) -> None:
        """
        Remove a state from the stack by its name.

        If the specified state is currently active (i.e., at the top of the stack),
        it will be popped using `pop_current_state()` to ensure proper resumption
        of the previous state. Otherwise, it will be removed directly from the stack.

        Parameters:
            state_name: The name of the state to remove.
        """
        try:
            matches = self.state_stack.get_states_by_name(state_name)
        except ValueError:
            logger.warning(f"No states found with name '{state_name}'")
            return

        for state in matches:
            if state == self.state_stack.current():
                logger.info(
                    f"State '{state_name}' is currently active. Automatically popping instead of removing."
                )
                self.pop_current_state()
            else:
                logger.debug(f"Removing state: {state.name}")
                self.state_stack.remove(state)
                state.shutdown()

    @overload
    def push_state(self, state_name: str, **kwargs: Any) -> State:
        pass

    @overload
    def push_state(
        self,
        state_name: State,
        **kwargs: Any,
    ) -> State:
        pass

    def push_state(
        self,
        state_name: str | State,
        **kwargs: Any,
    ) -> State:
        """
        Pause currently running state and start new one.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the ``__init__`` method of the
                new state.

        Returns:
            Instanced state.
        """
        logger.debug(f"push state: {state_name}")
        previous = self.current_state
        if previous is not None:
            self._check_resume(previous)
            previous.pause()

        if isinstance(state_name, State):
            instance = state_name
        elif isinstance(state_name, str):
            instance = self.state_factory.create_state(state_name, **kwargs)
        else:
            raise TypeError(
                "push_state no longer accepts State subclasses; "
                "pass a state instance or a state name string."
            )

        self.state_stack.push(instance)

        if self.has_listeners_for_event("on_state_change"):
            self.trigger_global_event("on_state_change")

        return instance

    @overload
    def replace_state(self, state_name: str, **kwargs: Any) -> State:
        pass

    @overload
    def replace_state(
        self,
        state_name: StateType,
        **kwargs: Any,
    ) -> StateType:
        pass

    def replace_state(
        self,
        state_name: str | State,
        **kwargs: Any,
    ) -> State:
        """
        Replace the currently running state with a new one.

        This is essentially, just a ``push_state``, followed by
        ``pop_state(running_state)``.
        This cannot be used to replace states in the middle of the stack.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the ``__init__`` method of the
                new state.

        Returns:
            Instanced state.
        """
        logger.debug(f"replace state: {state_name}")
        # raise error if stack is empty
        if not self.state_stack.all():
            raise RuntimeError(
                "Attempted to replace state when stack was empty."
            )

        previous = self.state_stack.current()
        instance = self.push_state(state_name, **kwargs)
        if previous is not None:
            self.pop_state(previous)
        return instance

    def push_state_with_timeout(
        self, state_name: str | StateType, updates: int = 1
    ) -> None:
        """
        Push a state onto the stack and schedule it to be destroyed after
        a specified number of updates.

        Parameters:
            state_name: The state to push onto the stack.
            updates: The number of updates after which the state will be
                destroyed.
        """
        state = self.push_state(state_name)
        state.task(lambda: self.pop_state(state), times=updates)

    @property
    def current_state(self) -> State | None:
        """Return the currently running state, if any."""
        return self.state_stack.current()

    @property
    def active_states(self) -> Sequence[State]:
        """Sequence of states that are active."""
        return self.state_stack.all()

    @property
    def queued_states(self) -> Sequence[QueuedState]:
        """Sequence of states that are queued."""
        return self.state_queue.queued_states

    @overload
    def get_state_by_name(self, state_name: str) -> State:
        pass

    @overload
    def get_state_by_name(
        self,
        state_name: type[StateType],
    ) -> StateType:
        pass

    def get_state_by_name(
        self,
        state_name: str | type[State],
    ) -> State:
        """
        Query the state stack for a state by the name supplied.

        Parameters:
            state_name: Name of a state.

        Returns:
            State with that name, if one exist. ``None`` otherwise.
        """
        for state in self.state_stack.all():
            if (
                state.__class__.__name__ == state_name
                or state.__class__ == state_name
            ):
                return state
        raise ValueError(f"Missing state {state_name}")

    def get_queued_state_by_name(self, state_name: str) -> QueuedState:
        """
        Query the queued state stack for a state by the name supplied.
        """
        return self.state_queue.get_queued_state_by_name(state_name)

    def get_active_state_names(self) -> Sequence[str]:
        """List of names of active states."""
        return [state.name for state in self.state_stack.all()]

    def clear_queued_states(self) -> None:
        """Clears all queued states."""
        self.state_queue.clear()

    def remove_queued_state_by_name(self, state_name: str) -> None:
        """Removes a queued state by name."""
        self.state_queue.remove_state_by_name(state_name)

    def remove_expired_queued_states(self) -> None:
        """Removes expired states from the queue based on their expiration time."""
        self.state_queue.remove_expired_states()

    def replace_queued_state(self, state_name: str, **new_kwargs: Any) -> None:
        """Replaces the arguments of a queued state."""
        self.state_queue.replace_queued_state(state_name, **new_kwargs)

    def peek_next_queued_state(
        self,
    ) -> QueuedState | None:
        """Returns the next queued state without removing it."""
        return self.state_queue.peek_next()
