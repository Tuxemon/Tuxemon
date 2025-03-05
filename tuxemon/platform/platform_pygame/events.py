from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator, Mapping
from typing import Any, ClassVar, Optional, TypedDict

import pygame as pg
from pygame.rect import Rect

from tuxemon import graphics, prepare
from tuxemon.platform.const import buttons, events
from tuxemon.platform.events import (
    EventQueueHandler,
    InputHandler,
    PlayerInput,
)
from tuxemon.session import local_session
from tuxemon.ui.draw import blit_alpha

HORIZONTAL_AXIS = 0
VERTICAL_AXIS = 1


class PygameEventQueueHandler(EventQueueHandler):
    """Handle all events from the pygame event queue."""

    def __init__(self) -> None:
        self._inputs: defaultdict[int, list[InputHandler[Any]]] = defaultdict(
            list
        )

    def add_input(self, player: int, handler: InputHandler[Any]) -> None:
        """
        Add an input handler to process.

        Parameters:
            player: Number of the player the handler belongs to.
            handler: Handler whose events will be processed from now on.

        """
        self._inputs[player].append(handler)

    def set_input(
        self,
        player: int,
        element: int,
        handler: InputHandler[Any],
    ) -> None:
        """
        Sets an input handler to process.

        Parameters:
            player: Number of the player the handler belongs to.
            element: Index to modify
            handler: Handler whose events will be processed from now on.
        """
        self._inputs[player][element] = handler

    def process_events(self) -> Generator[PlayerInput, None, None]:
        for pg_event in pg.event.get():
            for inputs in self._inputs.values():
                for player_input in inputs:
                    player_input.process_event(pg_event)

            if pg_event.type == pg.QUIT:
                local_session.client.event_engine.execute_action("quit")

        for inputs in self._inputs.values():
            for player_input in inputs:
                yield from player_input.get_events()


class PygameEventHandler(InputHandler[pg.event.Event]):
    """
    Input handler of Pygame events.
    """


class PygameGamepadInput(PygameEventHandler):
    """
    Gamepad event handler.

    NOTE: Due to implementation, you may receive "released" inputs for
    buttons/directions/axis even if they are released already. Pressed
    or held inputs will never be duplicated and are always "correct".

    Parameters:
        event_map: Mapping of original identifiers to button identifiers.
        deadzone: Threshold used to detect when an analog stick should
            be considered not pressed, as obtaining an exact value of 0 is
            almost impossible.

    """

    # Xbox 360 Controller buttons:
    # A = 0    Start = 7    D-Up = 13
    # B = 1    Back = 6     D-Down = 14
    # X = 2                 D-Left = 11
    # Y = 3                 D-Right = 12
    #
    default_input_map = {
        0: buttons.A,
        1: buttons.B,
        6: buttons.BACK,
        11: buttons.LEFT,
        12: buttons.RIGHT,
        13: buttons.UP,
        14: buttons.DOWN,
        7: buttons.START,
    }
    DEADZONE: float = 0.25

    def __init__(
        self,
        event_map: Optional[Mapping[Optional[int], int]] = None,
        deadzone: float = DEADZONE,
    ) -> None:
        super().__init__(event_map)
        self.deadzone = deadzone

    def is_within_deadzone(self, value: float) -> bool:
        """
        Checks if the axis value is within the deadzone.

        Parameters:
            value: The axis value.

        Returns:
            True if the value is within the deadzone, False otherwise.
        """
        return abs(value) < self.deadzone

    def handle_button(
        self, button: int, pressed: bool, value: float = 0.0
    ) -> None:
        """
        Handles button press or release events.

        Parameters:
            button: The button identifier.
            pressed: True if the button is pressed, False if released.
            value: The analog value of the button (optional, defaults to 0.0).
        """
        if pressed:
            self.press(button, value)
        else:
            self.release(button)

    def process_event(self, input_event: pg.event.Event) -> None:
        """
        Processes a pygame event.

        Parameters:
            input_event: The pygame event.
        """
        self.check_button(input_event)
        self.check_hat(input_event)
        self.check_axis(input_event)

    def check_button(self, pg_event: pg.event.Event) -> None:
        """
        Checks for button press/release events.

        Parameters:
            pg_event: The pygame event.
        """
        try:
            button = self.event_map[pg_event.button]
            self.handle_button(button, pg_event.type == pg.JOYBUTTONDOWN)
        except (KeyError, AttributeError):
            pass

    def check_hat(self, pg_event: pg.event.Event) -> None:
        """
        Checks for hat switch motion events.

        Parameters:
            pg_event: The pygame event.
        """
        if pg_event.type == pg.JOYHATMOTION:
            x, y = pg_event.value
            self.handle_button(buttons.LEFT, x == -1)
            self.handle_button(buttons.RIGHT, x == 1)
            # Note: y axis is inverted
            self.handle_button(buttons.DOWN, y == 1)
            # Note: y axis is inverted
            self.handle_button(buttons.UP, y == -1)
            if x == 0:
                self.handle_button(buttons.LEFT, False)
                self.handle_button(buttons.RIGHT, False)
            if y == 0:
                self.handle_button(buttons.UP, False)
                self.handle_button(buttons.DOWN, False)

    def check_axis(self, pg_event: pg.event.Event) -> None:
        """
        Checks for axis motion events.

        Parameters:
            pg_event: The pygame event.
        """
        if pg_event.type == pg.JOYAXISMOTION:
            self._handle_axis(pg_event.axis, pg_event.value)

    def _handle_axis(self, axis: int, value: float) -> None:
        """Handles axis motion events."""
        if self.is_within_deadzone(value):
            if axis == HORIZONTAL_AXIS:
                self.handle_button(buttons.LEFT, False)
                self.handle_button(buttons.RIGHT, False)
            elif axis == VERTICAL_AXIS:
                self.handle_button(buttons.UP, False)
                self.handle_button(buttons.DOWN, False)
            return

        if axis == HORIZONTAL_AXIS:
            self.handle_button(
                buttons.RIGHT if value > 0 else buttons.LEFT, True, abs(value)
            )
        elif axis == VERTICAL_AXIS:
            self.handle_button(
                buttons.DOWN if value > 0 else buttons.UP, True, abs(value)
            )


class PygameKeyboardInput(PygameEventHandler):
    """
    Keyboard event handler.

    Parameters:
        event_map: Mapping of original identifiers to button identifiers.

    """

    default_input_map = {
        pg.K_UP: buttons.UP,
        pg.K_DOWN: buttons.DOWN,
        pg.K_LEFT: buttons.LEFT,
        pg.K_RIGHT: buttons.RIGHT,
        pg.K_RETURN: buttons.A,
        pg.K_RSHIFT: buttons.B,
        pg.K_LSHIFT: buttons.B,
        pg.K_ESCAPE: buttons.BACK,
        pg.K_BACKSPACE: events.BACKSPACE,
        None: events.UNICODE,
    }

    def process_event(self, input_event: pg.event.Event) -> None:
        """
        Processes a pygame event.

        Parameters:
            input_event: The pygame event.
        """
        pressed = input_event.type == pg.KEYDOWN
        released = input_event.type == pg.KEYUP

        if pressed or released:
            self._handle_key_event(input_event, pressed)

    def _handle_key_event(
        self, input_event: pg.event.Event, pressed: bool
    ) -> None:
        """Handles key press or release events."""
        try:
            button = self.event_map[input_event.key]
        except KeyError:
            self._handle_unicode_event(input_event, pressed)
        else:
            if pressed:
                self.press(button)
            else:
                self.release(button)

    def _handle_unicode_event(
        self, input_event: pg.event.Event, pressed: bool
    ) -> None:
        """Handles Unicode input events."""
        try:
            if pressed:
                self.release(events.UNICODE)
                self.press(events.UNICODE, input_event.unicode)
            else:
                self.release(events.UNICODE)
        except AttributeError:
            pass


class DPadRectsInfo(TypedDict):
    up: Rect
    down: Rect
    left: Rect
    right: Rect


class DPadInfo(TypedDict):
    surface: pg.surface.Surface
    position: tuple[int, int]
    rect: DPadRectsInfo


class DPadButtonInfo(TypedDict):
    surface: pg.surface.Surface
    position: tuple[int, int]
    rect: Rect


class TouchOverlayUI:
    def __init__(self, transparency: int) -> None:
        self.transparency = transparency
        self.dpad: DPadInfo = {
            "surface": pg.Surface((0, 0)),
            "position": (0, 0),
            "rect": {
                "up": Rect(0, 0, 0, 0),
                "down": Rect(0, 0, 0, 0),
                "left": Rect(0, 0, 0, 0),
                "right": Rect(0, 0, 0, 0),
            },
        }
        self.a_button: DPadButtonInfo = {
            "surface": pg.Surface((0, 0)),
            "position": (0, 0),
            "rect": Rect(0, 0, 0, 0),
        }
        self.b_button: DPadButtonInfo = {
            "surface": pg.Surface((0, 0)),
            "position": (0, 0),
            "rect": Rect(0, 0, 0, 0),
        }
        self.load()

    def load(self) -> None:
        self.dpad["surface"] = graphics.load_and_scale("gfx/d-pad.png")
        self.dpad["position"] = (
            0,
            prepare.SCREEN_SIZE[1] - self.dpad["surface"].get_height(),
        )
        up = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 3),
            self.dpad["position"][1],
            self.dpad["surface"].get_width() / 3,
            self.dpad["surface"].get_height() / 2,
        )
        down = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 3),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2),
            self.dpad["surface"].get_width() / 3,
            self.dpad["surface"].get_height() / 2,
        )
        left = Rect(
            self.dpad["position"][0],
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 3),
            self.dpad["surface"].get_width() / 2,
            self.dpad["surface"].get_height() / 3,
        )
        right = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 2),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 3),
            self.dpad["surface"].get_width() / 2,
            self.dpad["surface"].get_height() / 3,
        )
        self.dpad["rect"] = {
            "up": up,
            "down": down,
            "left": left,
            "right": right,
        }

        self.a_button["surface"] = graphics.load_and_scale("gfx/a-button.png")
        self.a_button["position"] = (
            prepare.SCREEN_SIZE[0]
            - int(self.a_button["surface"].get_width() * 1.0),
            int(
                self.dpad["position"][1]
                + (self.dpad["surface"].get_height() / 2)
                - (self.a_button["surface"].get_height() / 2)
            ),
        )
        self.a_button["rect"] = Rect(
            self.a_button["position"][0],
            self.a_button["position"][1],
            self.a_button["surface"].get_width(),
            self.a_button["surface"].get_height(),
        )

        self.b_button["surface"] = graphics.load_and_scale("gfx/b-button.png")
        self.b_button["position"] = (
            prepare.SCREEN_SIZE[0]
            - int(self.b_button["surface"].get_width() * 2.1),
            int(
                self.dpad["position"][1]
                + (self.dpad["surface"].get_height() / 2)
                - (self.b_button["surface"].get_height() / 2)
            ),
        )
        self.b_button["rect"] = Rect(
            self.b_button["position"][0],
            self.b_button["position"][1],
            self.b_button["surface"].get_width(),
            self.b_button["surface"].get_height(),
        )

    def draw(self, screen: pg.surface.Surface) -> None:
        blit_alpha(
            screen,
            self.dpad["surface"],
            self.dpad["position"],
            self.transparency,
        )
        blit_alpha(
            screen,
            self.a_button["surface"],
            self.a_button["position"],
            self.transparency,
        )
        blit_alpha(
            screen,
            self.b_button["surface"],
            self.b_button["position"],
            self.transparency,
        )


class PygameTouchOverlayInput(PygameEventHandler):
    default_input_map: ClassVar[Mapping[Optional[int], int]] = {}

    def __init__(self, transparency: int) -> None:
        super().__init__()
        self.ui = TouchOverlayUI(transparency)
        self.buttons[buttons.UP] = PlayerInput(buttons.UP)
        self.buttons[buttons.DOWN] = PlayerInput(buttons.DOWN)
        self.buttons[buttons.LEFT] = PlayerInput(buttons.LEFT)
        self.buttons[buttons.RIGHT] = PlayerInput(buttons.RIGHT)
        self.buttons[buttons.A] = PlayerInput(buttons.A)
        self.buttons[buttons.B] = PlayerInput(buttons.B)
        self.load()

    def load(self) -> None:
        self.ui.load()

    def process_event(self, input_event: pg.event.Event) -> None:
        pressed = input_event.type == pg.MOUSEBUTTONDOWN
        released = input_event.type == pg.MOUSEBUTTONUP
        button = None
        if (pressed or released) and input_event.button == 1:
            mouse_pos = input_event.pos
            dpad_rect = self.ui.dpad["rect"]
            if dpad_rect["up"].collidepoint(mouse_pos):
                button = buttons.UP
            elif dpad_rect["down"].collidepoint(mouse_pos):
                button = buttons.DOWN
            elif dpad_rect["left"].collidepoint(mouse_pos):
                button = buttons.LEFT
            elif dpad_rect["right"].collidepoint(mouse_pos):
                button = buttons.RIGHT
            elif self.ui.a_button["rect"].collidepoint(mouse_pos):
                button = buttons.A
            elif self.ui.b_button["rect"].collidepoint(mouse_pos):
                button = buttons.B
        if pressed and button:
            self.press(button)
        elif released:
            for button in self.buttons:
                self.release(button)

    def draw(self, screen: pg.surface.Surface) -> None:
        self.ui.draw(screen)


class PygameMouseInput(PygameEventHandler):
    """
    Mouse event handler.

    Parameters:
        event_map: Mapping of original identifiers to button identifiers.

    """

    default_input_map = {
        pg.MOUSEBUTTONDOWN: buttons.MOUSELEFT,
        pg.MOUSEBUTTONUP: buttons.MOUSELEFT,
    }

    def process_event(self, pg_event: pg.event.Event) -> None:
        if pg_event.type == pg.MOUSEBUTTONDOWN:
            self.press(buttons.MOUSELEFT, pg_event.pos)
        elif pg_event.type == pg.MOUSEBUTTONUP:
            self.release(buttons.MOUSELEFT)
