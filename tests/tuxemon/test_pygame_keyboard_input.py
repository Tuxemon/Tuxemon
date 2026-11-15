# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame as pg
import pytest
from pygame.event import Event

from tuxemon.platform.const import buttons, events
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput


@pytest.fixture(scope="module", autouse=True)
def pygame_setup_teardown():
    pg.init()
    yield
    pg.quit()


@pytest.fixture
def keyboard_input() -> PygameKeyboardInput:
    kb = PygameKeyboardInput()
    kb.buttons[buttons.UP] = PlayerInput(buttons.UP)
    kb.buttons[buttons.A] = PlayerInput(buttons.A)
    kb.buttons[events.UNICODE] = PlayerInput(events.UNICODE)
    return kb


def test_key_press(keyboard_input: PygameKeyboardInput):
    keyboard_input.process_event(Event(pg.KEYDOWN, key=pg.K_UP))
    assert keyboard_input.buttons[buttons.UP].pressed


def test_key_release(keyboard_input: PygameKeyboardInput):
    keyboard_input.process_event(Event(pg.KEYDOWN, key=pg.K_UP))
    keyboard_input.process_event(Event(pg.KEYUP, key=pg.K_UP))
    assert not keyboard_input.buttons[buttons.UP].pressed


def test_mapped_key(keyboard_input: PygameKeyboardInput):
    keyboard_input.process_event(Event(pg.KEYDOWN, key=pg.K_RETURN))
    assert keyboard_input.buttons[buttons.A].pressed


def test_unicode_input(keyboard_input: PygameKeyboardInput):
    keyboard_input.process_event(Event(pg.KEYDOWN, unicode="a", key=pg.K_a))
    assert keyboard_input.buttons[events.UNICODE].pressed
    assert keyboard_input.buttons[events.UNICODE].value == "a"

    keyboard_input.process_event(Event(pg.KEYUP, key=pg.K_a))
    assert not keyboard_input.buttons[events.UNICODE].pressed


def test_unmapped_key(keyboard_input: PygameKeyboardInput):
    keyboard_input.process_event(Event(pg.KEYDOWN, key=pg.K_F1))
    assert not keyboard_input.buttons[buttons.UP].pressed
    assert not keyboard_input.buttons[buttons.A].pressed
    assert not keyboard_input.buttons[events.UNICODE].pressed


@pytest.mark.parametrize(
    "shift_key",
    [
        pytest.param(pg.K_RSHIFT, id="right_shift"),
        pytest.param(pg.K_LSHIFT, id="left_shift"),
    ],
)
def test_modifier_keys(keyboard_input: PygameKeyboardInput, shift_key: int):
    keyboard_input.process_event(Event(pg.KEYDOWN, key=shift_key))
    assert keyboard_input.buttons[buttons.B].pressed

    keyboard_input.process_event(Event(pg.KEYUP, key=shift_key))
    assert not keyboard_input.buttons[buttons.B].pressed


@pytest.mark.parametrize(
    "new_map, event, expected_button, expected_value, expected_pressed",
    [
        pytest.param(
            {pg.K_LEFT: buttons.A},
            Event(pg.KEYDOWN, key=pg.K_LEFT),
            buttons.A,
            None,
            True,
            id="add_new_button",
        ),
        pytest.param(
            {pg.K_DOWN: buttons.A},
            None,
            buttons.UP,
            None,
            False,
            id="remove_old_button",
        ),
        pytest.param(
            {None: events.UNICODE, pg.K_RETURN: buttons.A},
            Event(pg.KEYDOWN, unicode="x", key=pg.K_x),
            events.UNICODE,
            "x",
            True,
            id="unicode_preserved",
        ),
        pytest.param(
            {pg.K_RETURN: buttons.UP},
            Event(pg.KEYDOWN, key=pg.K_RETURN),
            buttons.UP,
            None,
            True,
            id="press_release_cycle_press",
        ),
    ],
)
def test_reload_mapping_behaviors(
    keyboard_input: PygameKeyboardInput,
    new_map,
    event,
    expected_button,
    expected_value,
    expected_pressed,
):
    keyboard_input.reload_mapping(new_map)
    keyboard_input.update_state(0)

    if event:
        keyboard_input.process_event(event)

    if expected_value is not None:
        assert keyboard_input.buttons[expected_button].value == expected_value

    if expected_pressed:
        assert keyboard_input.buttons[expected_button].pressed
    else:
        assert (
            expected_button not in keyboard_input.buttons
            or not keyboard_input.buttons[expected_button].pressed
        )

    # For press/release cycle, also check release
    if new_map == {pg.K_RETURN: buttons.UP}:
        keyboard_input.process_event(Event(pg.KEYUP, key=pg.K_RETURN))
        assert not keyboard_input.buttons[buttons.UP].pressed


def test_reload_mapping_is_deferred(keyboard_input: PygameKeyboardInput):
    old_map = dict(keyboard_input.event_map)
    new_map = {pg.K_LEFT: buttons.A}
    keyboard_input.reload_mapping(new_map)
    assert keyboard_input.event_map == old_map


def test_update_state_applies_pending_map(keyboard_input: PygameKeyboardInput):
    new_map = {pg.K_LEFT: buttons.A}
    keyboard_input.reload_mapping(new_map)
    keyboard_input.update_state(0)
    assert keyboard_input.event_map == new_map


def test_update_state_rebuilds_buttons(keyboard_input: PygameKeyboardInput):
    new_map = {pg.K_LEFT: buttons.A}
    keyboard_input.reload_mapping(new_map)
    keyboard_input.update_state(0)
    assert buttons.A in keyboard_input.buttons
    assert buttons.UP not in keyboard_input.buttons
