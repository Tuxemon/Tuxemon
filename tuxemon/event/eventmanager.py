# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Iterable
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.platform.input_manager import InputManager
    from tuxemon.state import StateManager

logger = logging.getLogger(__name__)


class EventManager:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def process_events(
        self, events: Iterable[PlayerInput]
    ) -> Generator[PlayerInput, None, None]:
        """
        Process and propagate events through active states.

        This method takes a sequence of player input events and passes
        each event through the active game states for processing. States
        can either modify the event, keep it (by returning None), or pass
        it along. If an event is kept, it does not propagate further. If
        it is returned, it will continue to the next state in the chain.

        After all states have processed the event, any unhandled events
        are forwarded to the event engine. The event engine can also
        modify, keep, or return the event. Finally, all unused events
        are stored in `Client.key_events` for further use in the system.

        Parameters:
            events: Iterable of player input events to process.

        Yields:
            Unprocessed events that were not kept by any state.
        """
        for game_event in events:
            if game_event:
                processed_event = self.propagate_event(game_event)
                if processed_event is not None:
                    game_event = processed_event
                if game_event:
                    yield game_event

    def propagate_event(
        self, game_event: PlayerInput
    ) -> Optional[PlayerInput]:
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

        for state in self.state_manager.active_states:
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
