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
    * Sole manager of platform events of type
    """

    _inputs: Mapping[int, Sequence[InputHandler[Any]]]

    def release_controls(self) -> Generator[PlayerInput, None, None]:
        """
        Send virtual input events which release held buttons/axis.

        After this frame, held/triggered inputs will return to previous state.

        Yields:
            Inputs to release all buttons.

        """
        for value in self._inputs.values():
            for inp in value:
                yield from inp.virtual_stop_events()

    @abstractmethod
    def process_events(self) -> Generator[PlayerInput, None, None]:
        """
        Process all pygame events.

        * Should never return pygame-unique events
        * All events returned should be Tuxemon game specific
        * This must be the only function to get events from the pygame event
          queue

        Yields:
            Game events.

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
        self.buttons = dict()
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
                inp.hold_time += 1
            elif inp.triggered:
                yield inp
                inp.triggered = False

    def press(self, button: int, value: float = 1) -> None:
        """
        Press a button managed by this handler.

        Parameters:
            button: Identifier of the button to press.
            value: Intensity value used for pressing the button.

        """
        inp = self.buttons[button]
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

    __slots__ = ("button", "value", "hold_time", "triggered")

    def __init__(
        self,
        button: int,
        value: Any = 0,
        hold_time: int = 0,
    ) -> None:
        self.button = button
        self.value = value
        self.hold_time = hold_time
        self.triggered = False

    def __str__(self) -> str:
        return (
            f"<PlayerInput: {self.button} {self.value} {self.pressed} "
            f"{self.held} {self.hold_time}>"
        )

    @property
    def pressed(self) -> bool:
        """
        This is edge triggered, meaning it will only be true once!

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
