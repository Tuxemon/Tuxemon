# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator, Mapping, Sequence
from typing import Any, ClassVar, Generic, Optional, TypeVar

_InputEventType = TypeVar("_InputEventType", contravariant=True)


class EventQueueHandler(ABC):
    """Event QueueHandler for different platforms.

    * Only one per game
    * Sole manager of platform events
    """

    _inputs: Mapping[int, Sequence[InputHandler[Any]]]

    def release_controls(self) -> Generator[PlayerInput, None, None]:
        """
        Send virtual input events which release held buttons/axis.

        After this frame, held/triggered inputs will return to previous state.
        Critically, this also updates the previous_value of the PlayerInput
        so that the released property works correctly in subsequent frames.

        Yields:
            Inputs to release all buttons.

        """
        for value in self._inputs.values():
            for input_handler in value:
                for player_input in input_handler.virtual_stop_events():
                    yield player_input
                    player_input.previous_value = player_input.value

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

    default_input_map: ClassVar[Mapping[Optional[int], int]]

    def __init__(
        self,
        event_map: Optional[Mapping[Optional[int], int]] = None,
    ) -> None:
        if event_map is None:
            event_map = self.default_input_map
        self.buttons = {}
        self.event_map = event_map
        for button in event_map.values():
            self.buttons[button] = PlayerInput(button)

    @abstractmethod
    def process_event(self, input_event: _InputEventType) -> None:
        """
        Process an input event, such as a Pygame event.

        Parameters:
            input_event: Input event to process.

        """
        raise NotImplementedError

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
        Update the input state (holding time, etc.) and return player inputs.

        Yields:
            Player inputs (before updating their state).

        """
        for inp in self.buttons.values():
            if inp.held:
                yield inp
                inp.previous_value = inp.value
                inp.hold_time += 1
            elif inp.triggered:
                yield inp
                inp.previous_value = inp.value
                inp.triggered = False

    def press(self, button: int, value: float = 1) -> None:
        """
        Press a button managed by this handler.

        Parameters:
            button: Identifier of the button to press.
            value: Intensity value used for pressing the button.

        """
        inp = self.buttons[button]
        inp.previous_value = inp.value
        inp.value = value
        if not inp.hold_time:
            inp.hold_time = 1

    def release(self, button: int) -> None:
        """
        Release a button managed by this handler.

        Parameters:
            button: Identifier of the button to release.

        """
        inp = self.buttons[button]
        inp.previous_value = inp.value
        inp.value = 0
        inp.hold_time = 0
        inp.triggered = True


class PlayerInput:
    """
    Represents a single player input.

    Each instance represents the state of a single input:
    * have float value 0-1
    * are "pressed" when value is above 0, for exactly one frame
    * are "held" when "pressed" for longer than zero frames
    Do not manipulate these values.
    Once created, these objects will not be destroyed.
    Input managers will set values on these objects.
    These objects are reused between frames, do not hold references to
    them.

    Parameters:
        button: Identifier of the button that caused this input.
        value: Value associated with the event. For buttons it is the
            intensity of the press in the range [0, 1]. 0 is not pressed
            and 1 is fully pressed. Some inputs, such as analog sticks may
            support intermediate or negative values. Other input may store
            the unicode key pressed, or the mouse coordinates.
        hold_time: The number of frames this input has been hold.

    """

    __slots__ = ("button", "value", "hold_time", "triggered", "previous_value")

    def __init__(
        self, button: int, value: Any = 0, hold_time: int = 0
    ) -> None:
        self.button = button
        self.value = value
        self.hold_time = hold_time
        self.triggered = False
        self.previous_value = value

    def __str__(self) -> str:
        return (
            f"PlayerInput("
            f"button={self.button}, "
            f"value={self.value}, "
            f"previous_value={self.previous_value}, "
            f"pressed={self.pressed}, "
            f"held={self.held}, "
            f"hold_time={self.hold_time}, "
            f"released={self.released}, "
            f"held_long={self.held_long}"
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
        This will be true as long as button is held down.

        Returns:
            Whether the input is being hold.

        """
        return bool(self.value)

    @property
    def released(self) -> bool:
        """
        Returns True *only* on the frame the button is released
        (value transitions from > 0 to 0).

        Returns:
            Whether the input has been released.
        """
        return bool(not self.value) and bool(self.previous_value)

    @property
    def held_long(self) -> bool:
        """
        Indicates whether the input has been held down for more than one frame.

        Returns:
            Whether the input has been held down for more than one frame.
        """
        return bool(self.value) and self.hold_time > 1

    def is_held(self, min_hold_time: int = 1) -> bool:
        """
        Returns True if the button is currently held for at least
        min_hold_time frames.
        """
        return self.held and self.hold_time >= min_hold_time
