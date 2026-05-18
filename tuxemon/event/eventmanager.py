# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Iterable
from typing import TYPE_CHECKING, TypeVar, cast

from tuxemon.event.eventmiddleware import EventMiddleware
from tuxemon.platform.events import PlayerInput

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus
    from tuxemon.platform.input_manager import InputManager
    from tuxemon.state.manager import StateManager

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=EventMiddleware)


class EventManager:
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self._event_bus = event_bus
        self._state_manager = state_manager
        self.middleware: dict[
            type[EventMiddleware], tuple[int, EventMiddleware]
        ] = {}

    def add_middleware(
        self, middleware_instance: EventMiddleware, priority: int = 100
    ) -> None:
        """
        Registers middleware with a priority.
        Lower priority = runs earlier in preprocess.
        Higher priority = runs later.
        """
        mw_type = type(middleware_instance)

        if mw_type in self.middleware:
            logger.warning(
                f"Middleware type {mw_type.__name__} already registered. Overwriting."
            )

        self.middleware[mw_type] = (priority, middleware_instance)

        self.middleware = dict(
            sorted(self.middleware.items(), key=lambda item: item[1][0])
        )

    def remove_middleware(self, middleware_instance: EventMiddleware) -> None:
        mw_type = type(middleware_instance)
        if mw_type in self.middleware:
            _, inst = self.middleware[mw_type]
            if inst is middleware_instance:
                del self.middleware[mw_type]

    def get_middleware_instance(self, middleware_type: type[T]) -> T | None:
        entry = self.middleware.get(middleware_type)
        if entry is None:
            return None
        return cast(T, entry[1])

    def process_events(
        self, events: Iterable[PlayerInput]
    ) -> Generator[PlayerInput, None, None]:
        """
        Process and propagate events through middleware and active states.

        Each raw event is first passed through all registered middleware
        via their `preprocess` methods. Middleware can modify the event
        or consume it by returning None. If consumed, the event does not
        continue further.

        Remaining events are then propagated through the active game states.
        States can modify the event or absorb it (return None). If absorbed,
        propagation stops.

        After state processing, the event is passed through all middleware
        again via their `postprocess` methods. Middleware can further modify
        or consume the event at this stage.

        Finally, any event that survives both middleware and state processing
        is yielded back to the caller.

        Parameters:
            events: Iterable of player input events to process.

        Yields:
            Events that were not consumed by middleware or states.
        """
        event: PlayerInput | None = None
        for raw_event in events:
            event = raw_event

            # PREPROCESS (in priority order)
            for _, mw in self.middleware.values():
                event = mw.preprocess(event)
                if event is None:
                    break
            if event is None:
                continue

            # STATE PROCESSING
            event = self.propagate_event(event)
            if event is None:
                continue

            # POSTPROCESS (reverse priority order)
            for _, mw in reversed(self.middleware.values()):
                event = mw.postprocess(event)
                if event is None:
                    break

            if event is not None:
                self._event_bus.publish("PLAYER_INPUT", event)
                yield event

    def propagate_event(self, game_event: PlayerInput) -> PlayerInput | None:
        """
        Propagates an event through active game states.

        This method passes an event through the state stack, allowing each
        active state to process and potentially modify it. If a state decides
        to keep the event (returns None), propagation stops. Otherwise, the
        event continues through the stack until a final processed version
        is returned or discarded.

        Parameters:
            game_event: The event to be processed.

        Returns:
            The final processed event if no state keeps it.
            If a state absorbs the event, returns ``None``.
        """
        final_event = game_event

        for state in self._state_manager.active_states:
            processed_event = state.process_event(final_event)

            if processed_event is None:
                return None

            final_event = processed_event

        return final_event

    def release_controls(
        self, input_manager: InputManager
    ) -> list[PlayerInput]:
        """
        Send inputs which release held buttons/axis

        Use to prevent player from holding buttons while state changes.
        """
        events = input_manager.event_queue.release_controls()
        return list(self.process_events(events))
