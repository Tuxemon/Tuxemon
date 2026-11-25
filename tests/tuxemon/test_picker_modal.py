# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""The number and quantity pickers are modal: no input reaches the menu below.

BACK used to fall through to the menu underneath, which began closing and
popped the picker instead of itself; it was left closed on top and the game
froze (storage > put an item in a box > BACK on the number picker).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.states.number_picker import NumberPickerState
from tuxemon.states.quantity import QuantityPickerState

PICKERS = [
    pytest.param(NumberPickerState, id="number_picker"),
    pytest.param(QuantityPickerState, id="quantity_picker"),
]
CANCEL = [
    pytest.param(buttons.B, id="b"),
    pytest.param(buttons.BACK, id="back"),
]
OTHER = [
    pytest.param(buttons.UP, id="up"),
    pytest.param(buttons.DOWN, id="down"),
    pytest.param(buttons.HOME, id="home"),
]


def _press(button: int) -> PlayerInput:
    return PlayerInput(button, value=1, hold_time=1)


@pytest.mark.parametrize("picker", PICKERS)
@pytest.mark.parametrize("button", CANCEL)
def test_cancel_closes_the_picker_and_stops_the_event(picker, button):
    state = MagicMock()
    state.valid_press.return_value = True
    assert picker.process_event(state, _press(button)) is None
    state.client.pop_state.assert_called_once()
    state.callback.assert_not_called()


@pytest.mark.parametrize("picker", PICKERS)
@pytest.mark.parametrize("button", OTHER)
def test_other_buttons_do_not_reach_the_menu_below(picker, button):
    state = MagicMock()
    state.valid_press.return_value = True
    assert picker.process_event(state, _press(button)) is None
    state.client.pop_state.assert_not_called()
