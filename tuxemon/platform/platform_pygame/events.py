# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional

import pygame as pg
from pygame.event import Event
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import graphics, prepare
from tuxemon.platform.const import buttons, events
from tuxemon.platform.events import (
    EventQueueHandler,
    InputHandler,
    PlayerInput,
)
from tuxemon.session import local_session
from tuxemon.ui.draw import blit_alpha

logger = logging.getLogger(__name__)

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


class InputMappingStrategy:
    def map_button(self, raw_button_id: int) -> Optional[int]:
        raise NotImplementedError

    def map_axis(
        self, axis_id: int, value: float
    ) -> tuple[Optional[int], bool]:
        raise NotImplementedError


class XboxMapping(InputMappingStrategy):
    def map_button(self, raw_button_id: int) -> Optional[int]:
        return {
            0: buttons.A,
            1: buttons.B,
            6: buttons.BACK,
            7: buttons.START,
            11: buttons.LEFT,
            12: buttons.RIGHT,
            13: buttons.UP,
            14: buttons.DOWN,
        }.get(raw_button_id)

    def map_axis(
        self, axis_id: int, value: float
    ) -> tuple[Optional[int], bool]:
        if axis_id == HORIZONTAL_AXIS:
            return (
                buttons.RIGHT if value > 0 else buttons.LEFT,
                abs(value) > 0.25,
            )
        elif axis_id == VERTICAL_AXIS:
            return (
                buttons.DOWN if value > 0 else buttons.UP,
                abs(value) > 0.25,
            )
        return (None, False)


class PlayStationMapping(InputMappingStrategy):
    def map_button(self, raw_button_id: int) -> Optional[int]:
        return {
            1: buttons.A,  # Cross
            2: buttons.B,  # Circle
            8: buttons.BACK,
            9: buttons.START,
            14: buttons.LEFT,
            15: buttons.RIGHT,
            12: buttons.UP,
            13: buttons.DOWN,
        }.get(raw_button_id)

    def map_axis(
        self, axis_id: int, value: float
    ) -> tuple[Optional[int], bool]:
        if axis_id == HORIZONTAL_AXIS:
            return (
                buttons.RIGHT if value > 0 else buttons.LEFT,
                abs(value) > 0.2,
            )
        elif axis_id == VERTICAL_AXIS:
            return (
                buttons.DOWN if value > 0 else buttons.UP,
                abs(value) > 0.2,
            )
        return (None, False)


class PygameEventHandler(InputHandler[Event]):
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

    def __init__(self, mapping_strategy: InputMappingStrategy):
        super().__init__({})
        self.mapping = mapping_strategy
        self.hat_state = (0, 0)
        self.axis_state = {HORIZONTAL_AXIS: 0, VERTICAL_AXIS: 0}

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
        logger.debug(
            f"{'Pressed' if pressed else 'Released'} {button} with value {value}"
        )
        if pressed:
            self.press(button, value)
        else:
            self.release(button)

    def process_event(self, input_event: Event) -> None:
        """
        Processes a pygame event.

        Parameters:
            input_event: The pygame event.
        """
        self.check_button(input_event)
        self.check_hat(input_event)
        self.handle_axis_event(input_event)

    def check_button(self, pg_event: Event) -> None:
        """
        Checks for button press/release events.

        Parameters:
            pg_event: The pygame event.
        """
        if pg_event.type in (pg.JOYBUTTONDOWN, pg.JOYBUTTONUP):
            button = self.mapping.map_button(pg_event.button)
            if button is not None:
                self.handle_button(button, pg_event.type == pg.JOYBUTTONDOWN)

    def check_hat(self, pg_event: Event) -> None:
        """
        Checks for hat switch motion events.

        Parameters:
            pg_event: The pygame event.
        """
        if pg_event.type == pg.JOYHATMOTION:
            x, y = pg_event.value
            prev_x, prev_y = self.hat_state
            self.hat_state = (x, y)

            if x != prev_x:
                self.handle_button(buttons.LEFT, x == -1)
                self.handle_button(buttons.RIGHT, x == 1)
                if prev_x == -1 and x != -1:
                    self.handle_button(buttons.LEFT, False)
                if prev_x == 1 and x != 1:
                    self.handle_button(buttons.RIGHT, False)

            if y != prev_y:
                self.handle_button(buttons.DOWN, y == 1)
                self.handle_button(buttons.UP, y == -1)
                if prev_y == 1 and y != 1:
                    self.handle_button(buttons.DOWN, False)
                if prev_y == -1 and y != -1:
                    self.handle_button(buttons.UP, False)

    def handle_axis_event(self, pg_event: Event) -> None:
        """
        Checks for axis motion events.

        Parameters:
            pg_event: The pygame event.
        """
        if pg_event.type == pg.JOYAXISMOTION:
            self._handle_axis(pg_event.axis, pg_event.value)

    def _handle_axis(self, axis: int, value: float) -> None:
        """Handles axis motion events."""
        button, pressed = self.mapping.map_axis(axis, value)
        if button is None:
            return

        # Determine direction: -1 (negative), 1 (positive), 0 (neutral)
        direction = 0
        if pressed:
            direction = 1 if value > 0 else -1

        # If direction hasn't changed, do nothing
        if self.axis_state[axis] == direction:
            return

        # Release previous direction
        if self.axis_state[axis] == -1:
            self.handle_button(
                buttons.LEFT if axis == HORIZONTAL_AXIS else buttons.UP, False
            )
        elif self.axis_state[axis] == 1:
            self.handle_button(
                buttons.RIGHT if axis == HORIZONTAL_AXIS else buttons.DOWN,
                False,
            )

        # Press new direction if applicable
        if direction != 0:
            self.handle_button(button, True, abs(value))

        # Update state
        self.axis_state[axis] = direction


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

    def process_event(self, input_event: Event) -> None:
        """
        Processes a pygame event.

        Parameters:
            input_event: The pygame event.
        """
        pressed = input_event.type == pg.KEYDOWN
        released = input_event.type == pg.KEYUP

        if pressed or released:
            self._handle_key_event(input_event, pressed)

    def _handle_key_event(self, input_event: Event, pressed: bool) -> None:
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

    def _handle_unicode_event(self, input_event: Event, pressed: bool) -> None:
        """Handles Unicode input events."""
        try:
            if pressed:
                self.release(events.UNICODE)
                self.press(events.UNICODE, input_event.unicode)
            else:
                self.release(events.UNICODE)
        except AttributeError:
            pass


DPAD_IMAGE = "gfx/d-pad.png"
A_BUTTON_IMAGE = "gfx/a-button.png"
B_BUTTON_IMAGE = "gfx/b-button.png"
A_BUTTON_SCALE = 1.0
B_BUTTON_SCALE = 2.1


@dataclass
class DPadRectsInfo:
    up: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
    down: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
    left: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
    right: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))


@dataclass
class DPadInfo:
    surface: Surface = field(default_factory=lambda: Surface((0, 0)))
    position: tuple[int, int] = (0, 0)
    rect: DPadRectsInfo = field(default_factory=DPadRectsInfo)


@dataclass
class DPadButtonInfo:
    surface: Surface = field(default_factory=lambda: Surface((0, 0)))
    position: tuple[int, int] = (0, 0)
    rect: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))


class TouchOverlayUI:
    def __init__(self, transparency: int) -> None:
        self.transparency = transparency
        self.dpad: DPadInfo
        self.a_button: DPadButtonInfo
        self.b_button: DPadButtonInfo
        self.load()

    def set_transparency(self, value: int) -> None:
        self.transparency = max(0, min(255, value))

    def load(self) -> None:
        """Loads the UI elements and re-initializes the frozen dataclasses."""

        dpad_surface = graphics.load_and_scale(DPAD_IMAGE)
        dpad_position = (
            0,
            prepare.SCREEN_SIZE[1] - dpad_surface.get_height(),
        )

        width, height = dpad_surface.get_width(), dpad_surface.get_height()
        pos_x, pos_y = dpad_position

        w3, h2, h3 = width // 3, height // 2, height // 3

        dpad_rects = DPadRectsInfo(
            up=Rect(pos_x + w3, pos_y, w3, h2),
            down=Rect(pos_x + w3, pos_y + h2, w3, h2),
            left=Rect(pos_x, pos_y + h3, width // 2, h3),
            right=Rect(pos_x + width // 2, pos_y + h3, width // 2, h3),
        )

        self.dpad = DPadInfo(
            surface=dpad_surface,
            position=dpad_position,
            rect=dpad_rects,
        )

        self.a_button = self._load_button_instance(
            A_BUTTON_IMAGE, A_BUTTON_SCALE
        )
        self.b_button = self._load_button_instance(
            B_BUTTON_IMAGE, B_BUTTON_SCALE
        )

    def _load_button_instance(
        self, image_path: str, scale: float
    ) -> DPadButtonInfo:
        """Helper to create and return a new DPadButtonInfo instance."""
        button_surface = graphics.load_and_scale(image_path)

        pos_y = int(
            self.dpad.position[1]
            + (self.dpad.surface.get_height() / 2)
            - (button_surface.get_height() / 2)
        )

        button_position = (
            prepare.SCREEN_SIZE[0] - int(button_surface.get_width() * scale),
            pos_y,
        )

        button_rect = Rect(
            button_position[0],
            button_position[1],
            button_surface.get_width(),
            button_surface.get_height(),
        )

        return DPadButtonInfo(
            surface=button_surface,
            position=button_position,
            rect=button_rect,
        )

    def draw(self, screen: Surface) -> None:
        """Draws the UI overlay."""
        blit_alpha(
            screen, self.dpad.surface, self.dpad.position, self.transparency
        )
        blit_alpha(
            screen,
            self.a_button.surface,
            self.a_button.position,
            self.transparency,
        )
        blit_alpha(
            screen,
            self.b_button.surface,
            self.b_button.position,
            self.transparency,
        )


class PygameTouchOverlayInput(PygameEventHandler):
    default_input_map: ClassVar[Mapping[Optional[int], int]] = {}

    def __init__(self, transparency: int) -> None:
        super().__init__()
        self.ui = TouchOverlayUI(transparency)
        self.buttons = {
            buttons.UP: PlayerInput(buttons.UP),
            buttons.DOWN: PlayerInput(buttons.DOWN),
            buttons.LEFT: PlayerInput(buttons.LEFT),
            buttons.RIGHT: PlayerInput(buttons.RIGHT),
            buttons.A: PlayerInput(buttons.A),
            buttons.B: PlayerInput(buttons.B),
        }
        self.load()

    def load(self) -> None:
        """Loads the UI elements."""
        self.ui.load()

    def process_event(self, input_event: Event) -> None:
        """Handles touch events."""
        if input_event.type not in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
            return

        mouse_pos = input_event.pos
        pressed = input_event.type == pg.MOUSEBUTTONDOWN

        button = self.get_touched_button(mouse_pos)
        if button is not None:
            if pressed:
                self.press(button)
            else:
                self.release(button)

    def get_touched_button(self, mouse_pos: tuple[int, int]) -> Optional[int]:
        """Determine which button was pressed based on position."""
        for name, rect in [
            (buttons.UP, self.ui.dpad.rect.up),
            (buttons.DOWN, self.ui.dpad.rect.down),
            (buttons.LEFT, self.ui.dpad.rect.left),
            (buttons.RIGHT, self.ui.dpad.rect.right),
            (buttons.A, self.ui.a_button.rect),
            (buttons.B, self.ui.b_button.rect),
        ]:
            if rect.collidepoint(mouse_pos):
                logger.debug(f"Touch detected on: {name}")
                return name
        return None

    def draw(self, screen: Surface) -> None:
        """Draws the UI overlay."""
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

    def process_event(self, pg_event: Event) -> None:
        if pg_event.type == pg.MOUSEBUTTONDOWN:
            self.press(buttons.MOUSELEFT, pg_event.pos)
        elif pg_event.type == pg.MOUSEBUTTONUP:
            self.release(buttons.MOUSELEFT)
