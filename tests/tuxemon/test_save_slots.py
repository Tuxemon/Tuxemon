# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.save_system.save_slots import (
    resolve_save_index,
    ui_to_save_index,
)


@pytest.mark.parametrize(
    "index, expected",
    [
        pytest.param(0, 1, id="ui0->slot1"),
        pytest.param(1, 2, id="ui1->slot2"),
        pytest.param(2, 3, id="ui2->slot3"),
    ],
)
def test_resolve_save_index_valid(index, expected):
    assert resolve_save_index(index) == expected


def test_resolve_save_index_none():
    with pytest.raises(ValueError):
        resolve_save_index(None)


@pytest.mark.parametrize(
    "ui_index, expected",
    [
        pytest.param(0, 1, id="ui0->slot1"),
        pytest.param(1, 2, id="ui1->slot2"),
        pytest.param(2, 3, id="ui2->slot3"),
    ],
)
def test_ui_to_save_index(ui_index, expected):
    assert ui_to_save_index(ui_index) == expected
