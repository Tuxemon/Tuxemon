# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Callable
from dataclasses import dataclass

import pygame as pg
import pytest
from pygame.event import Event
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import graphics
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import (
    DPAD_GAP_RATIO,
    PygameTouchOverlayInput,
)


@dataclass
class ButtonRectMapping:
    """Explicit mapping between a button and a rect accessor."""

    button: str
    rect_accessor: Callable[[PygameTouchOverlayInput], Rect]


@pytest.fixture(autouse=True)
def mock_load_and_scale(monkeypatch):
    monkeypatch.setattr(
        graphics, "load_and_scale", lambda filename: Surface((50, 50))
    )


@pytest.fixture
def touch_input() -> PygameTouchOverlayInput:
    ti = PygameTouchOverlayInput(128, (800, 600))
    for btn in [
        buttons.UP,
        buttons.DOWN,
        buttons.LEFT,
        buttons.RIGHT,
        buttons.A,
        buttons.B,
    ]:
        ti.buttons[btn] = PlayerInput(btn)
    ti.load()
    return ti


def normalized_pos(
    rect: Rect, resolution: tuple[int, int]
) -> tuple[float, float]:
    """Return normalized (x, y) position for a rect center."""
    return (
        rect.centerx / resolution[0],
        rect.centery / resolution[1],
    )


def test_mock_load_and_scale():
    surface = graphics.load_and_scale("dummy_file")
    assert isinstance(surface, Surface)
    assert surface.get_size() == (50, 50)


# Explicit mappings for dpad
@pytest.mark.parametrize(
    "mapping",
    [
        pytest.param(
            ButtonRectMapping(buttons.UP, lambda ti: ti.ui.dpad.rect.up),
            id="touch_dpad_up",
        ),
        pytest.param(
            ButtonRectMapping(buttons.DOWN, lambda ti: ti.ui.dpad.rect.down),
            id="touch_dpad_down",
        ),
        pytest.param(
            ButtonRectMapping(buttons.LEFT, lambda ti: ti.ui.dpad.rect.left),
            id="touch_dpad_left",
        ),
        pytest.param(
            ButtonRectMapping(buttons.RIGHT, lambda ti: ti.ui.dpad.rect.right),
            id="touch_dpad_right",
        ),
    ],
)
def test_touch_dpad(
    touch_input: PygameTouchOverlayInput, mapping: ButtonRectMapping
):
    x, y = normalized_pos(
        mapping.rect_accessor(touch_input), touch_input.resolution
    )
    event = Event(pg.FINGERDOWN, fingerid=1, x=x, y=y)
    touch_input.process_event(event)
    assert touch_input.buttons[mapping.button].pressed


# Explicit mappings for A/B buttons
button_mappings = [
    ButtonRectMapping(buttons.A, lambda ti: ti.ui.a_button.rect),
    ButtonRectMapping(buttons.B, lambda ti: ti.ui.b_button.rect),
]


@pytest.mark.parametrize(
    "mapping",
    [
        pytest.param(
            ButtonRectMapping(buttons.A, lambda ti: ti.ui.a_button.rect),
            id="touch_A_button",
        ),
        pytest.param(
            ButtonRectMapping(buttons.B, lambda ti: ti.ui.b_button.rect),
            id="touch_B_button",
        ),
    ],
)
def test_touch_buttons(
    touch_input: PygameTouchOverlayInput, mapping: ButtonRectMapping
):
    x, y = normalized_pos(
        mapping.rect_accessor(touch_input), touch_input.resolution
    )
    event = Event(pg.FINGERDOWN, fingerid=1, x=x, y=y)
    touch_input.process_event(event)
    assert touch_input.buttons[mapping.button].pressed


def test_touch_release(touch_input: PygameTouchOverlayInput):
    x, y = normalized_pos(touch_input.ui.dpad.rect.up, touch_input.resolution)
    touch_input.process_event(Event(pg.FINGERDOWN, fingerid=1, x=x, y=y))
    touch_input.process_event(Event(pg.FINGERUP, fingerid=1, x=x, y=y))
    assert not touch_input.buttons[buttons.UP].pressed


def test_touch_outside_buttons(touch_input: PygameTouchOverlayInput):
    event = Event(pg.FINGERDOWN, fingerid=1, x=10 / 800, y=10 / 600)
    touch_input.process_event(event)
    assert not any(btn.pressed for btn in touch_input.buttons.values())


def test_simultaneous_presses(touch_input: PygameTouchOverlayInput):
    up_x, up_y = normalized_pos(
        touch_input.ui.dpad.rect.up, touch_input.resolution
    )
    a_x, a_y = normalized_pos(
        touch_input.ui.a_button.rect, touch_input.resolution
    )
    events = [
        Event(pg.FINGERDOWN, fingerid=1, x=up_x, y=up_y),
        Event(pg.FINGERDOWN, fingerid=2, x=a_x, y=a_y),
    ]
    for e in events:
        touch_input.process_event(e)
    assert touch_input.buttons[buttons.UP].pressed
    assert touch_input.buttons[buttons.A].pressed


def test_touch_dead_zone(touch_input: PygameTouchOverlayInput):
    dpad_surface = touch_input.ui.dpad.surface
    pos_x, pos_y = touch_input.ui.dpad.position
    width, height = dpad_surface.get_size()

    gap_size = int(width * DPAD_GAP_RATIO)
    half_gap = gap_size // 2

    dead_zone_rect = Rect(
        pos_x + width // 2 - half_gap,
        pos_y + height // 2 - half_gap,
        gap_size,
        gap_size,
    )

    for point in [
        dead_zone_rect.center,
        (dead_zone_rect.left + 1, dead_zone_rect.top + 1),
        (dead_zone_rect.right - 1, dead_zone_rect.bottom - 1),
    ]:
        x, y = point[0] / 800, point[1] / 600
        touch_input.process_event(Event(pg.FINGERDOWN, fingerid=1, x=x, y=y))
        assert not any(btn.pressed for btn in touch_input.buttons.values())


def test_touch_on_border(touch_input: PygameTouchOverlayInput):
    border_pos = (
        touch_input.ui.dpad.rect.up.right,
        touch_input.ui.dpad.rect.down.top,
    )
    x, y = border_pos[0] / 800, border_pos[1] / 600
    event = Event(pg.FINGERDOWN, fingerid=1, x=x, y=y)
    touch_input.process_event(event)
    assert not touch_input.buttons[buttons.UP].pressed
    assert not touch_input.buttons[buttons.DOWN].pressed


def test_touch_outside_screen(touch_input: PygameTouchOverlayInput):
    x, y = 900 / 800, 700 / 600
    event = Event(pg.FINGERDOWN, fingerid=1, x=x, y=y)
    touch_input.process_event(event)
    assert not any(btn.pressed for btn in touch_input.buttons.values())


def test_persistent_press(touch_input: PygameTouchOverlayInput):
    x, y = normalized_pos(touch_input.ui.dpad.rect.up, touch_input.resolution)
    touch_input.process_event(Event(pg.FINGERDOWN, fingerid=1, x=x, y=y))
    assert touch_input.buttons[buttons.UP].pressed


def test_touch_dead_zone_border(touch_input: PygameTouchOverlayInput):
    dpad_surface = touch_input.ui.dpad.surface
    pos_x, pos_y = touch_input.ui.dpad.position
    width, height = dpad_surface.get_size()

    gap_size = int(width * DPAD_GAP_RATIO)
    half_gap = gap_size // 2

    dead_zone_rect = Rect(
        pos_x + width // 2 - half_gap,
        pos_y + height // 2 - half_gap,
        gap_size,
        gap_size,
    )

    border_points = [
        (dead_zone_rect.left - 1, dead_zone_rect.centery, buttons.LEFT),
        (dead_zone_rect.right + 1, dead_zone_rect.centery, buttons.RIGHT),
        (dead_zone_rect.centerx, dead_zone_rect.top - 1, buttons.UP),
        (dead_zone_rect.centerx, dead_zone_rect.bottom + 1, buttons.DOWN),
    ]

    for x, y, expected in border_points:
        nx, ny = x / 800, y / 600
        event = Event(pg.FINGERDOWN, fingerid=1, x=nx, y=ny)
        touch_input.process_event(event)
        assert touch_input.buttons[expected].pressed
