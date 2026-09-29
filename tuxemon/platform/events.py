# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Generator, Mapping
from typing import Any, ClassVar, Generic, TypeVar

_InputEventType = TypeVar("_InputEventType", contravariant=True)


class EventQueueHandler(ABC):
    """Event QueueHandler for different platforms.

    * Only one per game
    * Sole manager of platform events
    """

    def __init__(self) -> None:
        """Initialize instance-specific state."""
        self._inputs: defaultdict[int, dict[int, InputHandler[Any]]] = (
            defaultdict(dict)
        )
        self._filters: list[Callable[[PlayerInput], bool]] = []

    @property
    def filter_active(self) -> bool:
        return bool(self._filters)

    def set_input(
        self, player_id: int, index: int, input_handler: InputHandler[Any]
    ) -> None:
        """Add a new input device to be monitored for a specific player."""
        self._inputs[player_id][index] = input_handler

    def set_event_filter(
        self, filter_func: Callable[[PlayerInput], bool]
    ) -> None:
        self._filters.append(filter_func)

    def clear_event_filter(self) -> None:
        if not self._filters:
            return
        self._filters.pop()

    def get_input_handlers(self) -> Generator[InputHandler[Any], None, None]:
        """
        Yields all currently registered InputHandler instances across all players.
        """
        for player_handlers in self._inputs.values():
            yield from player_handlers.values()

    def release_controls(self) -> Generator[PlayerInput, None, None]:
        """
        Send virtual input events which release held buttons/axis.

        After this frame, held/triggered inputs will return to previous state.
        Critically, this also updates the previous_value of the PlayerInput
        so that the released property works correctly in subsequent frames.

        Yields:
            Inputs to release all buttons.
        """
        for input_handler in self.get_input_handlers():
            for player_input in input_handler.virtual_stop_events():
                yield player_input
                player_input.previous_value = player_input.value

    def update_handlers(self, time_delta: float) -> None:
        """
        Forwards the time delta to all registered InputHandlers,
        triggering state updates.
        """
        for handler in self.get_input_handlers():
            handler.update_state(time_delta)

    @abstractmethod
    def process_events(self) -> Generator[PlayerInput, None, None]:
        """
        Process all platform events.

        * Should never return platform-unique events
        * All events returned should be game specific
        * This must be the only function to get events from the platform
          event queue

        Yields:
            Game events (PlayerInput objects).
        """
        raise NotImplementedError


class InputHandler(ABC, Generic[_InputEventType]):
    """
    Enables basic input device with discrete inputs.

    Parameters:
        event_map: Mapping of original identifiers to button identifiers.
    """

    default_input_map: ClassVar[Mapping[int | None, int]]

    def __init__(
        self,
        event_map: Mapping[int | None, int] | None = None,
    ) -> None:
        if event_map is None:
            event_map = self.default_input_map
        self.buttons = {
            button: PlayerInput(button) for button in event_map.values()
        }
        self.event_map = event_map

    @abstractmethod
    def process_event(self, input_event: _InputEventType) -> None:
        """
        Process an input event, such as a Pygame event.

        Parameters:
            input_event: Input event to process.
        """
        raise NotImplementedError

    def update_state(self, dt: float) -> None:
        """
        Update the state of all managed PlayerInput objects.

        - Increments hold_time (frames) if held.
        - Increments hold_duration (seconds) by dt if held.
        - Resets both when released.
        """
        for inp in self.buttons.values():
            if inp.held:
                inp.hold_time += 1
                inp.hold_duration += dt
            else:
                inp.hold_time = 0
                inp.hold_duration = 0.0
            inp.previous_value = inp.value
            inp.triggered = False

    def virtual_stop_events(self) -> Generator[PlayerInput, None, None]:
        """
        Send virtual input events simulating released buttons/axis.
        This is used to force a state to release inputs without changing input
        state.

        Yields:
            Inputs to release all buttons of this handler.
        """
        for inp in self.buttons.values():
            if inp.held:
                inp.previous_value = inp.value
                yield PlayerInput(inp.button, 0, 0)

    def get_events(self) -> Generator[PlayerInput, None, None]:
        """
        Update the input state and return player inputs (as copies).

        Yields:
            A *new copy* of the PlayerInput object.
        """
        for inp in self.buttons.values():
            if inp.held or inp.triggered:
                yield inp.clone()
            if inp.held:
                inp.hold_time += 1
            inp.previous_value = inp.value
            inp.triggered = False

    def press(self, button: int, value: float = 1) -> None:
        """
        Press a button managed by this handler.

        Parameters:
            button: Identifier of the button to press.
            value: Intensity value used for pressing the button.
        """
        if button not in self.buttons:
            raise ValueError(f"Unknown button ID: {button}")
        inp = self.buttons[button]
        if inp.value == 0:
            inp.hold_time = 1
        inp.previous_value = inp.value
        inp.value = value
        inp.triggered = False

    def release(self, button: int) -> None:
        """
        Release a button managed by this handler.

        Parameters:
            button: Identifier of the button to release.
        """
        if button not in self.buttons:
            raise ValueError(f"Unknown button ID: {button}")
        inp = self.buttons[button]
        inp.previous_value = inp.value
        inp.value = 0
        inp.hold_time = 0
        inp.triggered = True


class PlayerInput:
    """
    Represents a single player input.

    Each instance tracks the state of a single input:
    * `value` is a float in the range [0, 1] indicating press intensity.
    * `pressed` is True only on the frame the input transitions from 0 → >0.
    * `held` is True as long as the input value remains >0.
    * `released` is True only on the frame the input transitions from >0 → 0.
    * `hold_time` counts how many update cycles (frames) the input has been
        held.
    * `hold_duration` accumulates the real-world time in seconds the input has
        been held, updated via `InputHandler.update_state(dt)`.

    Notes:
        - Do not manipulate these values directly; they are managed by input
            handlers.
        - PlayerInput objects are reused between frames and should not be
            stored long-term.
        - Input managers will set and update values automatically.

    Parameters:
        button: Identifier of the button that caused this input.
        value: Current intensity of the input. For buttons this is 0 (not
            pressed) or 1 (fully pressed). Analog inputs may use intermediate
            or negative values.
        hold_time: Number of frames the input has been held.
        hold_duration: Accumulated real-world time in seconds the input has
            been held. Updated each frame by InputHandler.update_state(dt).
    """

    __slots__ = (
        "button",
        "value",
        "hold_time",
        "triggered",
        "previous_value",
        "timestamp",
        "hold_duration",
    )

    def __init__(
        self,
        button: int,
        value: Any = 0,
        hold_time: int = 0,
        previous_value: Any = 0,
        timestamp: float | None = None,
        hold_duration: float = 0.0,
    ) -> None:
        self.button = button
        self.value = value
        self.hold_time = hold_time
        self.triggered: bool = False
        self.previous_value = previous_value
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.hold_duration = hold_duration

    def clone(self) -> PlayerInput:
        copy = PlayerInput(
            button=self.button,
            value=self.value,
            hold_time=self.hold_time,
            previous_value=self.previous_value,
            timestamp=self.timestamp,
            hold_duration=self.hold_duration,
        )
        copy.triggered = self.triggered
        return copy

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the essential state of the input into a dictionary for
        serialization.
        """

        def safe(v: Any) -> int | float | str:
            if isinstance(v, (int, float)):
                return v
            try:
                return float(v)
            except (TypeError, ValueError):
                return str(v)

        return {
            "button": self.button,
            "value": safe(self.value),
            "hold_time": self.hold_time,
            "previous_value": safe(self.previous_value),
            "timestamp": self.timestamp,
            "hold_duration": self.hold_duration,
        }

    def __str__(self) -> str:
        return (
            f"PlayerInput("
            f"button={self.button}, "
            f"value={self.value}, "
            f"previous_value={self.previous_value}, "
            f"pressed={self.pressed}, "
            f"held={self.held}, "
            f"hold_time={self.hold_time}, "
            f"hold_duration={self.hold_duration:.3f}, "
            f"released={self.released}"
            f")"
        )

    @property
    def pressed(self) -> bool:
        """
        Returns True *only* on the frame the button is initially pressed
        (value transitions from 0 to > 0).

        Returns:
            Whether the input has been pressed.
        """
        return bool(self.value) and self.hold_time == 1

    @property
    def held(self) -> bool:
        """
        Returns True as long as the button is held down (value > 0).
        """
        return bool(self.value)

    @property
    def released(self) -> bool:
        """
        Returns True *only* on the frame the button is released
        (value transitions from > 0 to 0).
        """
        return bool(not self.value) and bool(self.previous_value)

    def is_held(self, min_hold_duration: float = 0.0) -> bool:
        """
        Returns True if the button is currently held for at least
        min_hold_duration seconds (dt-based).
        """
        return self.held and self.hold_duration >= min_hold_duration
