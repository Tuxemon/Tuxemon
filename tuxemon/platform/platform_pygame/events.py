from __future__ import annotations
from collections import defaultdict

import pygame as pg
from pygame.rect import Rect

from tuxemon import graphics
from tuxemon.platform.const import buttons, events
from tuxemon.platform.events import (
    InputHandler,
    PlayerInput,
    EventQueueHandler,
)
from tuxemon.session import local_session
from tuxemon.ui.draw import blit_alpha
from typing import List, Dict, Generator, Optional, Mapping, Any, TypedDict,\
    Tuple
import pygame


class PygameEventQueueHandler(EventQueueHandler):
    """Handle all events from the pygame event queue."""

    def __init__(self) -> None:
        self._inputs: Dict[int, List[InputHandler[Any]]] = defaultdict(list)

    def add_input(self, player: int, handler: InputHandler[Any]) -> None:
        """
        Add an input handler to process.

        Parameters:
            player: Number of the player the handler belongs to.
            handler: Handler whose events will be processed from now on.

        """
        self._inputs[player].append(handler)

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


class PygameEventHandler(InputHandler[pygame.event.Event]):
    """
    Input handler of Pygame events.
    """
    pass


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

    def __init__(
        self,
        event_map: Optional[Mapping[Optional[int], int]] = None,
        deadzone: float = 0.25,
    ) -> None:
        super().__init__(event_map)
        self.deadzone = deadzone

    def process_event(self, input_event: pygame.event.Event) -> None:
        self.check_button(input_event)
        self.check_hat(input_event)
        self.check_axis(input_event)

    def check_button(self, pg_event: pygame.event.Event) -> None:
        try:
            button = self.event_map[pg_event.button]
            if pg_event.type == pg.JOYBUTTONDOWN:
                self.press(button)
            elif pg_event.type == pg.JOYBUTTONUP:
                self.release(button)
        except (KeyError, AttributeError):
            pass

    def check_hat(self, pg_event: pygame.event.Event) -> None:
        if pg_event.type == pg.JOYHATMOTION:
            x, y = pg_event.value
            if x == -1:
                self.press(buttons.LEFT, value=x * -1)
            elif x == 0:
                self.release(buttons.LEFT)
                self.release(buttons.RIGHT)
            elif x == 1:
                self.press(buttons.RIGHT)

            if y == -1:
                self.press(buttons.DOWN, value=y * -1)
            elif y == 0:
                self.release(buttons.DOWN)
                self.release(buttons.UP)
            elif y == 1:
                self.press(buttons.UP)

    def check_axis(self, pg_event: pygame.event.Event) -> None:
        if pg_event.type == pg.JOYAXISMOTION:
            value = pg_event.value

            if pg_event.axis == 0:
                if abs(value) >= self.deadzone:
                    if value < 0:
                        self.press(buttons.LEFT, value * -1)
                    else:
                        self.press(buttons.RIGHT, value)
                else:
                    self.release(buttons.LEFT)
                    self.release(buttons.RIGHT)

            elif pg_event.axis == 1:
                if abs(value) >= self.deadzone:
                    if value < 0:
                        self.press(buttons.UP, value * -1)
                    else:
                        self.press(buttons.DOWN, value)
                else:
                    self.release(buttons.UP)
                    self.release(buttons.DOWN)


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

    def process_event(self, input_event: pygame.event.Event) -> None:

        pressed = input_event.type == pg.KEYDOWN
        released = input_event.type == pg.KEYUP

        if pressed or released:
            # try to get game-specific action for the key
            try:
                button = self.event_map[input_event.key]
            except KeyError:
                pass
            else:
                if pressed:
                    self.press(button)
                else:
                    self.release(button)
                return

            # just get unicode value
            try:
                if pressed:
                    self.release(events.UNICODE)
                    self.press(events.UNICODE, input_event.unicode)
                else:
                    self.release(events.UNICODE)
            except AttributeError:
                pass


# TODO: Someone should refactor these to proper classes.
class DPadRectsInfo(TypedDict):
    up: Rect
    down: Rect
    left: Rect
    right: Rect


class DPadInfo(TypedDict):
    surface: pygame.surface.Surface
    position: Tuple[int, int]
    rect: DPadRectsInfo


class DPadButtonInfo(TypedDict):
    surface: pygame.surface.Surface
    position: Tuple[int, int]
    rect: Rect


class PygameTouchOverlayInput(PygameEventHandler):
    """
    Touch overlay event handler.

    Parameters:
        transparency: Transparency of the drawn overlay.

    """
    default_input_map: Mapping[Optional[int], int] = {}

    def __init__(self, transparency: int) -> None:
        super().__init__()
        self.transparency = transparency
        self.dpad: DPadInfo = {}  # type: ignore
        self.a_button: DPadButtonInfo = {}  # type: ignore
        self.b_button: DPadButtonInfo = {}  # type: ignore
        # TODO: try to simplify this
        self.buttons[buttons.UP] = PlayerInput(buttons.UP)
        self.buttons[buttons.DOWN] = PlayerInput(buttons.DOWN)
        self.buttons[buttons.LEFT] = PlayerInput(buttons.LEFT)
        self.buttons[buttons.RIGHT] = PlayerInput(buttons.RIGHT)
        self.buttons[buttons.A] = PlayerInput(buttons.A)
        self.buttons[buttons.B] = PlayerInput(buttons.B)

    def process_event(self, input_event: pygame.event.Event) -> None:
        """
        Process a Pygame event.

        Process all events from the controller overlay and pass them down to
        current State. All controller overlay events are converted to keyboard
        events for compatibility. This is primarily used for the mobile version
        of Tuxemon.

        Will probably be janky with multi touch.

        Parameters:
            input_event: Input event to process.

        """
        pressed = input_event.type == pg.MOUSEBUTTONDOWN
        released = input_event.type == pg.MOUSEBUTTONUP
        button = None

        if (pressed or released) and input_event.button == 1:
            mouse_pos = input_event.pos
            dpad_rect = self.dpad["rect"]

            if dpad_rect["up"].collidepoint(mouse_pos):
                button = buttons.UP
            elif dpad_rect["down"].collidepoint(mouse_pos):
                button = buttons.DOWN
            elif dpad_rect["left"].collidepoint(mouse_pos):
                button = buttons.LEFT
            elif dpad_rect["right"].collidepoint(mouse_pos):
                button = buttons.RIGHT
            elif self.a_button["rect"].collidepoint(mouse_pos):
                button = buttons.A
            elif self.b_button["rect"].collidepoint(mouse_pos):
                button = buttons.B

        if pressed and button:
            self.press(button)
        elif released:
            for button in self.buttons:
                self.release(button)

    def load(self) -> None:
        """Load the touch overlay attributes."""
        from tuxemon import prepare

        self.dpad["surface"] = graphics.load_and_scale("gfx/d-pad.png")
        self.dpad["position"] = (
            0,
            prepare.SCREEN_SIZE[1] - self.dpad["surface"].get_height(),
        )

        # Create the collision rectangle objects for the dpad so we can see
        # if we're pressing a button
        self.dpad["rect"] = {}  # type: ignore
        self.dpad["rect"]["up"] = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 3),
            self.dpad["position"][1],  # Rectangle position_y
            self.dpad["surface"].get_width() / 3,  # Rectangle size_x
            self.dpad["surface"].get_height() / 2,
        )  # Rectangle size_y
        self.dpad["rect"]["down"] = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 3),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 2),
            self.dpad["surface"].get_width() / 3,
            self.dpad["surface"].get_height() / 2,
        )
        self.dpad["rect"]["left"] = Rect(
            self.dpad["position"][0],
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 3),
            self.dpad["surface"].get_width() / 2,
            self.dpad["surface"].get_height() / 3,
        )
        self.dpad["rect"]["right"] = Rect(
            self.dpad["position"][0] + (self.dpad["surface"].get_width() / 2),
            self.dpad["position"][1] + (self.dpad["surface"].get_height() / 3),
            self.dpad["surface"].get_width() / 2,
            self.dpad["surface"].get_height() / 3,
        )

        # Create the buttons
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

    def draw(self, screen: pygame.surface.Surface) -> None:
        """
        Draws the controller overlay to the screen.

        Parameters:
            screen: Screen surface to draw onto.

        """
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

    def process_event(self, pg_event: pygame.event.Event) -> None:
        if pg_event.type == pg.MOUSEBUTTONDOWN:
            self.press(buttons.MOUSELEFT, pg_event.pos)
        elif pg_event.type == pg.MOUSEBUTTONUP:
            self.release(buttons.MOUSELEFT)
