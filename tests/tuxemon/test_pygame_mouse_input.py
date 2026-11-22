# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame as pg
import pytest
from pygame.event import Event

from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameMouseInput


@pytest.fixture(scope="module", autouse=True)
def pygame_setup_teardown():
    pg.init()
    yield
    pg.quit()


@pytest.fixture
def mouse_input() -> PygameMouseInput:
    mi = PygameMouseInput()
    mi.buttons[buttons.MOUSELEFT] = PlayerInput(buttons.MOUSELEFT)
    return mi


def test_mouse_button_down(mouse_input: PygameMouseInput):
    event = Event(pg.MOUSEBUTTONDOWN, button=1, pos=(10, 20))
    mouse_input.process_event(event)
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed
    assert mouse_input.buttons[buttons.MOUSELEFT].value == (10, 20)


def test_mouse_button_up(mouse_input: PygameMouseInput):
    mouse_input.process_event(
        Event(pg.MOUSEBUTTONDOWN, button=1, pos=(10, 20))
    )
    mouse_input.process_event(Event(pg.MOUSEBUTTONUP, button=1, pos=(10, 20)))
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(1, id="mouse_button_1"),
        pytest.param(2, id="mouse_button_2"),
        pytest.param(3, id="mouse_button_3"),
    ],
)
def test_other_mouse_buttons(mouse_input: PygameMouseInput, button: int):
    mouse_input.process_event(
        Event(pg.MOUSEBUTTONDOWN, button=button, pos=(50, 60))
    )
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed

    mouse_input.process_event(
        Event(pg.MOUSEBUTTONUP, button=button, pos=(50, 60))
    )
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


def test_multiple_clicks(mouse_input: PygameMouseInput):
    for pos in [(5, 5), (15, 25)]:
        mouse_input.process_event(Event(pg.MOUSEBUTTONDOWN, button=1, pos=pos))
        assert mouse_input.buttons[buttons.MOUSELEFT].pressed
        assert mouse_input.buttons[buttons.MOUSELEFT].value == pos
        mouse_input.process_event(Event(pg.MOUSEBUTTONUP, button=1, pos=pos))
        assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


def test_release_without_press(mouse_input: PygameMouseInput):
    mouse_input.process_event(Event(pg.MOUSEBUTTONUP, button=1, pos=(0, 0)))
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


def test_unhandled_event_type(mouse_input: PygameMouseInput):
    event = Event(pg.JOYAXISMOTION, axis=0, value=0.5)
    mouse_input.process_event(event)
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


def test_double_click(mouse_input: PygameMouseInput):
    pos1 = (100, 200)
    pos2 = (120, 220)

    mouse_input.process_event(Event(pg.MOUSEBUTTONDOWN, button=1, pos=pos1))
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed
    assert mouse_input.buttons[buttons.MOUSELEFT].value == pos1

    mouse_input.process_event(Event(pg.MOUSEBUTTONDOWN, button=1, pos=pos2))
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed
    assert mouse_input.buttons[buttons.MOUSELEFT].value == pos2

    mouse_input.process_event(Event(pg.MOUSEBUTTONUP, button=1, pos=pos2))
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed


def test_gpu_upscaler_converts_window_position(
    mouse_input: PygameMouseInput, monkeypatch: pytest.MonkeyPatch
):
    from dataclasses import replace

    from tuxemon import prepare

    fit = prepare.FrameFit.compute((1280, 720), (768, 432))
    context = replace(
        prepare.DISPLAY_CONTEXT,
        gpu_upscaling=True,
        window_size=(1280, 720),
        window_to_screen=fit.window_to_screen,
    )
    monkeypatch.setattr(prepare, "DISPLAY_CONTEXT", context)

    event = Event(pg.MOUSEBUTTONDOWN, button=1, pos=(640, 360))
    mouse_input.process_event(event)
    assert mouse_input.buttons[buttons.MOUSELEFT].value == (384, 216)


def test_drag_updates_position(mouse_input: PygameMouseInput):
    start_pos = (30, 40)
    mouse_input.process_event(
        Event(pg.MOUSEBUTTONDOWN, button=1, pos=start_pos)
    )
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed
    assert mouse_input.buttons[buttons.MOUSELEFT].value == start_pos

    drag_pos = (60, 80)
    mouse_input.process_event(
        Event(pg.MOUSEBUTTONDOWN, button=1, pos=drag_pos)
    )
    assert mouse_input.buttons[buttons.MOUSELEFT].pressed
    assert mouse_input.buttons[buttons.MOUSELEFT].value == drag_pos

    mouse_input.process_event(Event(pg.MOUSEBUTTONUP, button=1, pos=drag_pos))
    assert not mouse_input.buttons[buttons.MOUSELEFT].pressed
