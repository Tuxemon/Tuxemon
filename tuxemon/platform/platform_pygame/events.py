# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from typing import ClassVar

import pygame as pg
from pygame.event import Event
from pygame.joystick import JoystickType
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import graphics
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
        super().__init__()

    def process_events(self) -> Generator[PlayerInput, None, None]:
        for pg_event in pg.event.get():
            for input_handler in self.get_input_handlers():
                input_handler.process_event(pg_event)

            if pg_event.type == pg.QUIT:
                local_session.client.event_engine.execute_action("quit")

        for input_handler in self.get_input_handlers():
            for event in input_handler.get_events():
                if all(f(event) for f in self._filters):
                    yield event


class InputMappingStrategy:
    def map_button(self, raw_button_id: int) -> int | None:
        raise NotImplementedError

    def map_axis(self, axis_id: int, value: float) -> tuple[int | None, bool]:
        raise NotImplementedError


class XboxMapping(InputMappingStrategy):
    def map_button(self, raw_button_id: int) -> int | None:
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

    def map_axis(self, axis_id: int, value: float) -> tuple[int | None, bool]:
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
    def map_button(self, raw_button_id: int) -> int | None:
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

    def map_axis(self, axis_id: int, value: float) -> tuple[int | None, bool]:
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


class KeyBindingRules:
    RESERVED_KEYS = {
        pg.K_ESCAPE,
        pg.K_RETURN,
        pg.K_BACKSPACE,
        pg.K_LSHIFT,
        pg.K_RSHIFT,
        pg.K_UP,
        pg.K_DOWN,
        pg.K_LEFT,
        pg.K_RIGHT,
    }

    @classmethod
    def is_valid_binding(cls, key: int) -> bool:
        return key not in cls.RESERVED_KEYS


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
        mapping_strategy: An InputMappingStrategy instance used to convert
            raw pygame identifiers (button indices, axis indices, hat values)
            into logical button identifiers used by the game.
    """

    def __init__(
        self,
        mapping_strategy: InputMappingStrategy,
        joysticks: list[JoystickType],
    ):
        super().__init__({})
        self.mapping = mapping_strategy
        self.joysticks = joysticks
        self.hat_state = (0, 0)
        self.axis_state = {HORIZONTAL_AXIS: 0, VERTICAL_AXIS: 0}

        for js in self.joysticks:
            try:
                # No js.init() here
                instance_id = js.get_instance_id()
                logger.info(f"Using joystick with instance ID {instance_id}")
            except Exception as e:
                logger.warning(f"Failed to access joystick instance ID: {e}")

    def _is_our_joystick(self, pg_event: Event) -> bool:
        return any(
            js.get_instance_id() == pg_event.joy for js in self.joysticks
        )

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
            if not self._is_our_joystick(pg_event):
                return

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
            if not self._is_our_joystick(pg_event):
                return

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
            if not self._is_our_joystick(pg_event):
                return

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

    def __init__(
        self, event_map: Mapping[int | None, int] | None = None
    ) -> None:
        super().__init__(event_map or self.default_input_map)
        self._initialize_buttons_from_map(self.event_map)
        self._needs_rebuild: bool = False
        self._pending_map: Mapping[int | None, int] | None = None

    def update_state(self, dt: float) -> None:
        if self._needs_rebuild:
            assert self._pending_map is not None
            self.event_map = self._pending_map
            self._initialize_buttons_from_map(self._pending_map)
            self._needs_rebuild = False

        super().update_state(dt)

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

    def reload_mapping(self, new_map: Mapping[int | None, int]) -> None:
        """Update the key→button mapping in place."""
        self._pending_map = new_map
        self._needs_rebuild = True

    def _initialize_buttons_from_map(
        self, mapping: Mapping[int | None, int]
    ) -> None:
        """Ensure self.buttons matches the given mapping."""
        for button in mapping.values():
            if button not in self.buttons:
                self.buttons[button] = PlayerInput(button)

        for button in list(self.buttons.keys()):
            if button not in mapping.values():
                del self.buttons[button]

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


# +-----------------------+
# |         UP            |
# |   +---------------+   |
# |   |               |   |
# | L |     GAP       | R |
# | E |   (dead zone) | I |
# | F |               | G |
# | T +---------------+ H |
# |         DOWN          |
# +-----------------------+


DPAD_IMAGE = "gfx/d-pad.png"
A_BUTTON_IMAGE = "gfx/a-button.png"
B_BUTTON_IMAGE = "gfx/b-button.png"
A_BUTTON_SCALE = 1.0
B_BUTTON_SCALE = 2.1
DPAD_GAP_RATIO = 0.2


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
    def __init__(self, transparency: int, resolution: tuple[int, int]) -> None:
        self.transparency = transparency
        self.resolution = resolution
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
            self.resolution[1] - dpad_surface.get_height(),
        )

        width, height = dpad_surface.get_width(), dpad_surface.get_height()
        pos_x, pos_y = dpad_position

        gap_size = int(width * DPAD_GAP_RATIO)
        half_gap = gap_size // 2

        w_arm = width - gap_size  # Total width of the horizontal arms (L+R)
        h_arm = height - gap_size  # Total height of the vertical arms (U+D)

        dpad_rects = DPadRectsInfo(
            up=Rect(pos_x + half_gap, pos_y, width - gap_size, h_arm // 2),
            down=Rect(
                pos_x + half_gap,
                pos_y + height - h_arm // 2,
                width - gap_size,
                h_arm // 2,
            ),
            left=Rect(pos_x, pos_y + half_gap, w_arm // 2, height - gap_size),
            right=Rect(
                pos_x + width - w_arm // 2,
                pos_y + half_gap,
                w_arm // 2,
                height - gap_size,
            ),
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
            self.resolution[0] - int(button_surface.get_width() * scale),
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
    default_input_map: ClassVar[Mapping[int | None, int]] = {}

    def __init__(self, transparency: int, resolution: tuple[int, int]) -> None:
        super().__init__()
        self.ui = TouchOverlayUI(transparency, resolution)
        self.resolution = resolution
        self.buttons = {
            buttons.UP: PlayerInput(buttons.UP),
            buttons.DOWN: PlayerInput(buttons.DOWN),
            buttons.LEFT: PlayerInput(buttons.LEFT),
            buttons.RIGHT: PlayerInput(buttons.RIGHT),
            buttons.A: PlayerInput(buttons.A),
            buttons.B: PlayerInput(buttons.B),
        }
        self.load()
        self._active_touches: dict[int, int] = {}

    def load(self) -> None:
        """Loads the UI elements."""
        self.ui.load()

    def process_event(self, input_event: Event) -> None:
        """Handles both mouse and finger touch events."""

        if input_event.type in (pg.FINGERDOWN, pg.FINGERUP, pg.FINGERMOTION):
            touch_pos = (
                int(input_event.x * self.resolution[0]),
                int(input_event.y * self.resolution[1]),
            )
            finger_id = input_event.fingerid

            if input_event.type == pg.FINGERDOWN:
                self._handle_finger_down(finger_id, touch_pos)
            elif input_event.type == pg.FINGERUP:
                self._handle_finger_up(finger_id)
            elif input_event.type == pg.FINGERMOTION:
                self._handle_finger_motion(finger_id, touch_pos)

    def _handle_finger_down(
        self, finger_id: int, touch_pos: tuple[int, int]
    ) -> None:
        button = self.get_touched_button(touch_pos)
        if button is not None:
            if button not in self._active_touches.values():
                self.press(button)
            self._active_touches[finger_id] = button

    def _handle_finger_up(self, finger_id: int) -> None:
        if finger_id in self._active_touches:
            button = self._active_touches[finger_id]
            del self._active_touches[finger_id]
            if button not in self._active_touches.values():
                self.release(button)

    def _handle_finger_motion(
        self, finger_id: int, touch_pos: tuple[int, int]
    ) -> None:
        if finger_id in self._active_touches:
            current_button = self._active_touches[finger_id]
            new_button = self.get_touched_button(touch_pos)

            if new_button != current_button:
                if current_button not in self._active_touches.values():
                    self.release(current_button)

                if new_button is not None:
                    if new_button not in self._active_touches.values():
                        self.press(new_button)
                    self._active_touches[finger_id] = new_button
                else:
                    del self._active_touches[finger_id]

    def get_touched_button(self, pos: tuple[int, int]) -> int | None:
        """Determine which button was pressed based on position."""
        for name, rect in [
            (buttons.UP, self.ui.dpad.rect.up),
            (buttons.DOWN, self.ui.dpad.rect.down),
            (buttons.LEFT, self.ui.dpad.rect.left),
            (buttons.RIGHT, self.ui.dpad.rect.right),
            (buttons.A, self.ui.a_button.rect),
            (buttons.B, self.ui.b_button.rect),
        ]:
            if rect.collidepoint(pos):
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
