# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Listener:
    priority: int
    callback: Callable[..., None] = field(compare=False)


class EventBus:
    """
    A central event bus for broadcasting events to registered listeners.

    This class allows different parts of the application to communicate
    without direct coupling, by subscribing to and publishing events.
    """

    def __init__(self) -> None:
        """
        Initializes the EventBus.
        _listeners: Stores event names mapped to a list of Listener objects.
        """
        self._listeners: dict[str, list[Listener]] = {}

    def subscribe(
        self, event_name: str, listener: Callable[..., None], priority: int = 0
    ) -> None:
        """
        Subscribes a listener function to a specified event.

        Parameters:
            event_name: The unique name of the event (non-empty string).
            listener: A callable function that will be invoked when the event is published.
            priority: Execution priority (higher number means earlier execution, default is 0).

        Raises:
            ValueError: If the event_name is empty or listener is not callable.
        """
        if not isinstance(event_name, str) or not event_name:
            raise ValueError("Event name must be a non-empty string.")
        if not callable(listener):
            raise ValueError("Listener must be callable.")

        if event_name not in self._listeners:
            self._listeners[event_name] = []

        self._listeners[event_name].append(Listener(priority, listener))
        self._listeners[event_name].sort(
            key=lambda l: l.priority, reverse=True
        )

    def unsubscribe(
        self,
        event_name: str,
        listener: Callable[..., None],
        priority: int | None = None,
    ) -> None:
        """
        Unsubscribes a listener function from a specified event.

        Parameters:
            event_name: The unique name of the event.
            listener: The listener function to remove.
            priority: The priority of the listener (optional). If provided, only a listener
                      with a matching priority and callback will be removed.

        Raises:
            ValueError: If the event does not exist.
        """
        if event_name not in self._listeners:
            logger.warning(
                f"Tried to unsubscribe from non-existent event '{event_name}'"
            )
            return

        self._listeners[event_name] = [
            l
            for l in self._listeners[event_name]
            if not (
                l.callback == listener
                and (priority is None or l.priority == priority)
            )
        ]

        if not self._listeners[event_name]:
            del self._listeners[event_name]

    def publish(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Publishes an event, invoking all subscribed listener functions for that
        event name, passing in any additional arguments.

        Parameters:
            event_name: The name of the event to publish.
            *args: Additional positional arguments to pass to the listeners.
            **kwargs: Additional keyword arguments to pass to the listeners.
        """
        if event_name not in self._listeners:
            return

        for listener in list(self._listeners[event_name]):
            try:
                listener.callback(*args, **kwargs)
            except Exception as e:
                name = getattr(
                    listener.callback, "__name__", repr(listener.callback)
                )
                logger.error(
                    f"Error in event listener for '{event_name}' ({name}): {e}",
                    exc_info=True,
                )

    def debug_events(self) -> None:
        """Log all registered events and their listeners."""
        for name, listeners in self._listeners.items():
            logger.debug(f"Event: {name}")
            for listener in listeners:
                listener_name = getattr(
                    listener.callback, "__name__", repr(listener.callback)
                )
                logger.debug(
                    f"  Priority {listener.priority}: {listener_name}"
                )

    def clear_event(self, event_name: str) -> None:
        """Removes all listeners associated with the specified event."""
        if event_name in self._listeners:
            del self._listeners[event_name]
            logger.debug(f"Cleared all listeners for event '{event_name}'")
        else:
            logger.warning(f"Tried to clear non-existent event '{event_name}'")

    def reset_all_events(self) -> None:
        """Resets (clears) all registered events and their listeners."""
        logger.debug(f"Resetting all {len(self._listeners)} events")
        self._listeners.clear()

    def has_listeners_for_event(self, event_name: str) -> bool:
        """
        Checks if any listeners are registered for the given event name.
        """
        return event_name in self._listeners
